from app import db
from app.models import SessionMessage, StudySession, User
from app.models.associations import joined_sessions, saved_sessions


def seed_demo_data(reset=False):
    if reset:
        reset_demo_data()
    elif StudySession.query.count() > 0:
        return 0

    student = User.query.filter_by(username="hlionar").first()
    if student is None:
        student = User(
            first_name="Hans",
            last_name="Lionar",
            username="hlionar",
            email="24661999@student.uwa.edu.au",
            uwa_id="24661999",
            role=User.ROLE_STUDENT,
        )
        student.set_password("passwd")

    lecturer = User.query.filter_by(username="MatthewDaggitt").first()
    if lecturer is None:
        lecturer = User(
            first_name="Matthew",
            last_name="Daggitt",
            username="MatthewDaggitt",
            email="matthew.daggitt@uwa.edu.au",
            role=User.ROLE_LECTURER,
        )
        lecturer.set_password("passwd")

    admin = User.query.filter_by(username="admin").first()
    if admin is None:
        admin = User(
            first_name="Admin",
            last_name="User",
            username="admin",
            email="admin@cshub.local",
            role=User.ROLE_ADMIN,
        )
        admin.set_password("admin")

    db.session.add_all([student, lecturer, admin])
    db.session.commit()

    demo_sessions = build_demo_sessions(student, lecturer, admin)
    db.session.add_all(demo_sessions)
    db.session.commit()

    student.joined.extend([demo_sessions[0], demo_sessions[2], demo_sessions[4]])
    lecturer.joined.extend([demo_sessions[1], demo_sessions[5]])
    admin.joined.append(demo_sessions[3])

    student.saved.extend([demo_sessions[1], demo_sessions[5]])
    lecturer.saved.append(demo_sessions[4])
    admin.saved.append(demo_sessions[0])
    db.session.commit()

    return len(demo_sessions)


def reset_demo_data():
    db.session.execute(joined_sessions.delete())
    db.session.execute(saved_sessions.delete())
    SessionMessage.query.delete()
    StudySession.query.delete()
    User.query.delete()
    db.session.commit()


def build_demo_sessions(student, lecturer, admin):
    return [
        StudySession(
            unit_code="CITS5508",
            topic="Machine Learning Revision Group",
            description="Review supervised learning, model evaluation, and common exam-style machine learning questions.",
            host_name=student.full_name,
            day="Mon",
            time="10:00 AM",
            mode="online",
            capacity=6,
            joined_count=2,
            host_id=student.id,
        ),
        StudySession(
            unit_code="CITS5505",
            topic="Agile Web Development Sprint",
            description="Work through Flask routes, SQLAlchemy models, Jinja templates, testing, and final project polish.",
            host_name=lecturer.full_name,
            day="Tue",
            time="2:00 PM",
            mode="hybrid",
            capacity=8,
            joined_count=1,
            host_id=lecturer.id,
        ),
        StudySession(
            unit_code="CITS5504",
            topic="Data Warehousing Study Session",
            description="Revise data warehouse design, dimensional modelling, ETL concepts, and analytics workflows.",
            host_name=student.full_name,
            day="Wed",
            time="4:30 PM",
            mode="in-person",
            capacity=5,
            joined_count=2,
            host_id=student.id,
        ),
        StudySession(
            unit_code="CITS4401",
            topic="Software Requirements and Design Workshop",
            description="Compare use cases, acceptance criteria, architecture decisions, and UI flow diagrams.",
            host_name=admin.full_name,
            day="Thu",
            time="11:00 AM",
            mode="online",
            capacity=4,
            joined_count=1,
            host_id=admin.id,
        ),
        StudySession(
            unit_code="CITS4404",
            topic="Artificial Intelligence Problem Solving",
            description="Practise search strategies, knowledge representation, and reasoning problems with classmates.",
            host_name=student.full_name,
            day="Fri",
            time="3:00 PM",
            mode="hybrid",
            capacity=6,
            joined_count=2,
            host_id=student.id,
        ),
        StudySession(
            unit_code="CITS4403",
            topic="Computational Modelling Review",
            description="Discuss modelling assumptions, simulation results, and how to explain computational experiments clearly.",
            host_name=lecturer.full_name,
            day="Sat",
            time="1:00 PM",
            mode="online",
            capacity=5,
            joined_count=1,
            host_id=lecturer.id,
        ),
    ]
