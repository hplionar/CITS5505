from pathlib import Path
import sys

# ------------------------------------------------------------
# Allow this script to be run directly from the project root.
# Example:
#   python scripts/seed_dev_db.py
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, db
from app.models import User, StudySession, ForumThread, ForumReply, ForumTag


def create_demo_users():
    """Create demo users for local development and testing."""

    student = User(
        first_name="Hans",
        last_name="Lionar",
        username="hlionar",
        email="24661999@student.uwa.edu.au",
        uwa_id="24661999",
        role=User.ROLE_STUDENT,
    )
    student.set_password("passwd")

    lecturer = User(
        first_name="Matthew",
        last_name="Daggitt",
        username="MatthewDaggitt",
        email="matthew.daggitt@uwa.edu.au",
        role=User.ROLE_LECTURER,
    )
    lecturer.set_password("passwd")

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

    return student, lecturer, admin


def create_demo_forum_tags():
    """Create the forum tags that users can select when creating a thread."""

    tags = {
        "study-tips": ForumTag(name="Study Tips", slug="study-tips"),
        "cits5505": ForumTag(name="CITS5505", slug="cits5505"),
        "exam-prep": ForumTag(name="Exam Prep", slug="exam-prep"),
        "mvc": ForumTag(name="MVC", slug="mvc"),
        "flask": ForumTag(name="Flask", slug="flask"),
        "web-development": ForumTag(name="Web Development", slug="web-development"),
        "machine-learning": ForumTag(name="Machine Learning", slug="machine-learning"),
        "pca": ForumTag(name="PCA", slug="pca"),
        "intuition": ForumTag(name="Intuition", slug="intuition"),
    }

    db.session.add_all(tags.values())
    db.session.commit()

    return tags


def create_demo_study_sessions(student, lecturer, admin):
    """Create demo Study Buddy data connected to the demo users."""

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

    # Demonstrate joined/saved session relationships.
    student.joined.append(demo_session)
    lecturer.saved.append(demo_session)
    admin.saved.append(demo_session)

    db.session.commit()


def create_demo_forum_data(student, lecturer, admin, tags):
    """Create demo forum threads and replies for local development.

    The first three threads preserve the original forum.js mock examples.
    Hans is the student asking the questions, and Matthew replies as the lecturer.
    """

    thread_exam = ForumThread(
        title="How are you preparing for the CITS5508 Machine Learning exam?",
        body=(
            "How are you preparing for the CITS5508 Machine Learning exam since there’s no cheat sheet allowed? "
            "Any tips appreciated.\n\n"
            "Inspired by a real r/UWA thread: https://www.reddit.com/r/uwa/comments/1t1jad6/cits_5508_machine_learning/"
        ),
        category="General",
        author=student,
        is_pinned=True,
    )

    thread_mvc = ForumThread(
        title="I still do not really understand Model-View-Controller",
        body=(
            "I keep seeing Model-View-Controller explained as Model for data, View for UI, "
            "and Controller for application logic. But in our actual Flask project, I am not sure "
            "how to map that idea properly. For example, are the SQLAlchemy classes in models.py "
            "the Model? Are Jinja templates the View? And are the route functions the Controller? "
            "I think I understand the words, but not how the pieces connect in a real codebase."
        ),
        category="Software Engineering",
        author=student,
    )

    thread_pca = ForumThread(
        title="I still do not really understand the idea behind PCA",
        body=(
            "I understand that PCA is used for dimensionality reduction, but I am still confused "
            "about the intuition. When we say PCA finds directions of maximum variance, does that "
            "mean it is finding the most important features? How should I think about principal "
            "components in a simple way, especially when the original dataset has many columns?"
        ),
        category="AI & Data Science",
        author=student,
    )

    db.session.add_all([thread_exam, thread_mvc, thread_pca])
    db.session.flush()

    # Attach predetermined tags to demo threads.
    thread_exam.tags.extend([
        tags["study-tips"],
        tags["machine-learning"],
        tags["exam-prep"],
    ])

    thread_mvc.tags.extend([
        tags["cits5505"],
        tags["mvc"],
        tags["web-development"],
    ])

    thread_pca.tags.extend([
        tags["machine-learning"],
        tags["pca"],
        tags["intuition"],
    ])

    # Demo persisted likes/saves.
    thread_exam.liked_by.append(lecturer)
    thread_exam.liked_by.append(admin)
    thread_exam.saved_by.append(lecturer)

    thread_mvc.liked_by.append(lecturer)
    thread_mvc.saved_by.append(student)

    thread_pca.liked_by.append(lecturer)
    thread_pca.liked_by.append(admin)
    thread_pca.saved_by.append(admin)

    replies = [
        ForumReply(
            body=(
                "For the ML exam, focus on the core ideas first: what each model is trying to optimise, "
                "how to interpret the outputs, and why the evaluation metrics matter. Practising short "
                "written explanations will probably help more than memorising code."
            ),
            thread=thread_exam,
            author=lecturer,
        ),
        ForumReply(
            body=(
                "You are thinking about MVC in the right direction. In this Flask project, the SQLAlchemy "
                "classes are the Model because they represent database entities, the Jinja templates are "
                "the View because they define what the user sees, and the route functions act like the "
                "Controller because they receive requests, call the model, and choose which template to render."
            ),
            thread=thread_mvc,
            author=lecturer,
        ),
        ForumReply(
            body=(
                "A simple way to think about PCA is that it finds new directions through the data where the "
                "values vary the most. These directions are not usually the original columns themselves, but "
                "combinations of them. Keeping the first few principal components lets you keep much of the "
                "structure while reducing the number of dimensions."
            ),
            thread=thread_pca,
            author=lecturer,
        ),
    ]

    db.session.add_all(replies)
    db.session.commit()


def seed_dev_db():
    """Reset and seed the development database.

    WARNING:
    This deletes all existing local database data.
    Use this only for development/testing, not production.
    """

    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        student, lecturer, admin = create_demo_users()
        tags = create_demo_forum_tags()

        create_demo_study_sessions(student, lecturer, admin)
        create_demo_forum_data(student, lecturer, admin, tags)

        print("Development database initialized.")
        print("Test users:")
        print("  hlionar / passwd")
        print("  matthew.daggitt@uwa.edu.au / passwd")
        print("  admin / admin")


if __name__ == "__main__":
    seed_dev_db()