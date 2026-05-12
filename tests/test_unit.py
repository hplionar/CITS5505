import json
import re

from app import db
from app.models import SessionMessage, SessionReadState, StudySession, User


def test_register_creates_user_with_hashed_password(client, app):
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password1",
            "confirm_password": "Password1",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.password_hash != "Password1"
        assert user.check_password("Password1")


def test_register_rejects_duplicate_username(client):
    response = client.post(
        "/register",
        data={
            "username": "student",
            "email": "another@example.com",
            "password": "Password1",
            "confirm_password": "Password1",
        },
    )

    assert response.status_code == 200
    assert b"Username unavailable" in response.data


def test_login_and_logout_flow(client):
    response = client.post(
        "/login",
        data={"identifier": "student", "password": "Password1"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome back" in response.data

    response = client.post("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"Log In" in response.data


def test_studybuddy_requires_login(client):
    response = client.get("/studybuddy")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_resource_pages_require_login(client):
    for path in ("/help", "/rules"):
        response = client.get(path)

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_resource_pages_render_for_logged_in_user(auth_client):
    response = auth_client.get("/help")

    assert response.status_code == 200
    assert b"Common tasks" in response.data
    assert b"Study Buddy" in response.data

    response = auth_client.get("/rules")

    assert response.status_code == 200
    assert b"CSHub Rules" in response.data
    assert b"academic integrity" in response.data


def test_create_session_persists_and_auto_joins_host(auth_client, app):
    response = auth_client.post(
        "/studybuddy/create",
        data={
            "unit_code": "cits5505",
            "topic": "Unit Test Session",
            "description": "Created during a unit test.",
            "host_name": "Study Student",
            "session_date": "2026-05-18",
            "time": "10:00 AM",
            "mode": "hybrid",
            "location": "EZONE North 1.24",
            "capacity": "4",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        session = StudySession.query.filter_by(topic="Unit Test Session").one()
        user = User.query.filter_by(username="student").one()
        assert session.unit_code == "CITS5505"
        assert session.session_date.isoformat() == "2026-05-18"
        assert session.day == "Mon"
        assert session.location == "EZONE North 1.24"
        assert session.host_id == user.id
        assert session in user.joined


def test_join_leave_save_and_unsave_session(auth_client, app):
    with app.app_context():
        session_id = StudySession.query.filter_by(topic="Seeded Study Session").one().id

    auth_client.post(f"/sessions/{session_id}/join")
    auth_client.post(f"/sessions/{session_id}/save")

    with app.app_context():
        user = User.query.filter_by(username="student").one()
        session = db.session.get(StudySession, session_id)
        assert session in user.joined
        assert session in user.saved

    auth_client.post(f"/sessions/{session_id}/leave")
    auth_client.post(f"/sessions/{session_id}/unsave")

    with app.app_context():
        user = User.query.filter_by(username="student").one()
        session = db.session.get(StudySession, session_id)
        assert session not in user.joined
        assert session not in user.saved


def test_joined_session_is_available_as_calendar_reminder(auth_client, app):
    with app.app_context():
        session = StudySession.query.filter_by(topic="Seeded Study Session").one()
        session_id = session.id
        expected_reminder_date = session.session_date.isoformat()

    auth_client.post(f"/sessions/{session_id}/join")
    response = auth_client.get("/home")

    match = re.search(
        rb'<script id="joinedSessionsData" type="application/json">\s*(.*?)\s*</script>',
        response.data,
        re.S,
    )

    assert match is not None

    joined_sessions_data = json.loads(match.group(1))
    reminder = next(
        session_data
        for session_data in joined_sessions_data
        if session_data["id"] == session_id
    )

    assert reminder["topic"] == "Seeded Study Session"
    assert reminder["time"] == "4:00 PM"
    assert reminder["reminder_date"] == expected_reminder_date


def test_messages_and_replies_are_persisted(auth_client, app):
    with app.app_context():
        session_id = StudySession.query.filter_by(topic="Seeded Study Session").one().id

    auth_client.post(f"/sessions/{session_id}/join")
    auth_client.post(f"/sessions/{session_id}/messages", data={"content": "What should we revise?"})

    with app.app_context():
        message = SessionMessage.query.filter_by(content="What should we revise?").one()
        message_id = message.id

    auth_client.post(
        f"/sessions/{session_id}/messages/{message_id}/reply",
        data={"content": "Start with the project rubric."},
    )

    with app.app_context():
        reply = SessionMessage.query.filter_by(content="Start with the project rubric.").one()
        assert reply.parent_id == message_id
        assert reply.session_id == session_id


def test_session_notifications_clear_after_viewing_session(auth_client, app):
    with app.app_context():
        session = StudySession.query.filter_by(topic="Seeded Study Session").one()
        student = User.query.filter_by(username="student").one()
        session_id = session.id
        student_id = student.id

    auth_client.post(f"/sessions/{session_id}/join")

    with app.app_context():
        host = User.query.filter_by(username="host").one()
        message = SessionMessage(
            session_id=session_id,
            user_id=host.id,
            content="Please check the shared notes.",
        )
        db.session.add(message)
        db.session.commit()

    response = auth_client.get("/home")
    assert b"1 new" in response.data
    assert b"notification-badge" in response.data
    assert b"Please check the shared notes." in response.data

    auth_client.get(f"/sessions/{session_id}")

    with app.app_context():
        read_state = SessionReadState.query.filter_by(
            user_id=student_id,
            session_id=session_id,
        ).one()
        first_read_message_id = read_state.last_read_message_id

    response = auth_client.get("/home")
    assert b"0 new" in response.data
    assert b"notification-badge" not in response.data

    with app.app_context():
        host = User.query.filter_by(username="host").one()
        message = SessionMessage(
            session_id=session_id,
            user_id=host.id,
            content="I added one more example.",
        )
        db.session.add(message)
        db.session.commit()

    response = auth_client.get("/home")
    assert b"1 new" in response.data
    assert b"notification-badge" in response.data
    assert b"I added one more example." in response.data

    with app.app_context():
        read_state = SessionReadState.query.filter_by(
            user_id=student_id,
            session_id=session_id,
        ).one()
        assert read_state.last_read_message_id == first_read_message_id
