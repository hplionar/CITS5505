from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text

from app import create_app, db
from app.models import User, StudySession


def clear_dev_data():
    """
    Clear development data without dropping the database schema.

    The schema should be created/updated using:
        flask db upgrade
    """

    # Delete child/dependent tables first to avoid foreign key issues.
    db.session.execute(text("DELETE FROM session_message"))
    db.session.execute(text("DELETE FROM joined_sessions"))
    db.session.execute(text("DELETE FROM saved_sessions"))
    db.session.execute(text("DELETE FROM study_session"))
    db.session.execute(text("DELETE FROM user"))
    db.session.commit()


def seed_dev_db():
    app = create_app()

    with app.app_context():
        clear_dev_data()

        student = User(
            first_name="Hans",
            last_name="Lionar",
            username="hlionar",
            email="24661999@student.uwa.edu.au",
            uwa_id="24661999",
            role=User.ROLE_STUDENT,
        )
        student.set_password("passwd123")

        lecturer = User(
            first_name="Matthew",
            last_name="Daggitt",
            username="MatthewDaggitt",
            email="matthew.daggitt@uwa.edu.au",
            role=User.ROLE_LECTURER,
        )
        lecturer.set_password("passwd123")

        admin = User(
            first_name="Admin",
            last_name="User",
            username="admin",
            email="admin@cshub.local",
            role=User.ROLE_ADMIN,
        )
        admin.set_password("admin123")

        db.session.add_all([student, lecturer, admin])
        db.session.commit()

        demo_session = StudySession(
            unit_code="CITS5505",
            topic="Authentication Backend Test",
            description="Demo session for testing users and login validation later.",
            host_name=student.full_name,
            day="Fri",
            time="4:00 PM",
            mode="online",
            capacity=5,
            joined_count=1,
            host_id=student.id,
        )

        db.session.add(demo_session)
        db.session.commit()

        student.joined.append(demo_session)
        lecturer.saved.append(demo_session)
        admin.saved.append(demo_session)
        db.session.commit()

        print("Development database seeded.")
        print("Test users:")
        print("  hlionar / passwd123")
        print("  matthew.daggitt@uwa.edu.au / passwd123")
        print("  admin / admin123")


if __name__ == "__main__":
    seed_dev_db()