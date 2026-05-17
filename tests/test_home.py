import re

from app import db
from app.models import User, StudySession, SessionMessage


def login_client(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "homeuser"


def test_home_activity_count_uses_backend_data(client, app):
    with app.app_context():
        user = User(
            username="homeuser",
            email="homeuser@example.com",
            role=User.ROLE_STUDENT,
        )
        user.set_password("Password123")

        db.session.add(user)
        db.session.commit()

        study_session = StudySession(
            unit_code="CITS5505",
            topic="Backend Stability Study Session",
            description="Testing Home dashboard activity count.",
            host_name="Tutor",
            day="Monday",
            time="2:00 PM",
            mode="hybrid",
            location="Library",
            capacity=6,
            joined_count=1,
            host_id=user.id,
        )

        db.session.add(study_session)
        db.session.commit()

        user.joined.append(study_session)
        user.saved.append(study_session)

        message = SessionMessage(
            session_id=study_session.id,
            user_id=user.id,
            content="This is a test activity message."
        )

        db.session.add(message)
        db.session.commit()

        user_id = user.id

    login_client(client, user_id)

    response = client.get("/home")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "Backend Stability Study Session" in html
    assert "This is a test activity message" in html
    assert re.search(r'data-testid="activity-count">\s*3\s*</h2>', html)