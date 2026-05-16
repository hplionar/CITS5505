from pathlib import Path
import sys

# ------------------------------------------------------------
# Allow this script to be run directly from the project root.
# Example:
#   python scripts/seed_dev_db.py
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text

from app import create_app, db
from app.seed import seed_demo_data
from app.models import User, ForumThread, ForumReply, ForumTag
from app.models.associations import (
    forum_thread_tags,
    liked_forum_threads,
    saved_forum_threads,
)


def get_or_create_user(
    username,
    email,
    password,
    role,
    first_name=None,
    last_name=None,
    uwa_id=None,
):
    """Return an existing user by username, or create it if missing."""
    user = User.query.filter_by(username=username).first()

    if user is not None:
        return user

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        uwa_id=uwa_id,
        role=role,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return user


def clear_forum_data():
    """Clear forum demo data before reseeding forum content."""
    db.session.execute(forum_thread_tags.delete())
    db.session.execute(liked_forum_threads.delete())
    db.session.execute(saved_forum_threads.delete())

    ForumReply.query.delete()
    ForumThread.query.delete()
    ForumTag.query.delete()

    db.session.commit()


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


def create_demo_forum_data(student, lecturer, admin, vraparla, qwang, tags):
    """Create demo forum threads and replies for local development."""
    thread_exam = ForumThread(
        title="How are you preparing for the CITS5508 Machine Learning exam?",
        body=(
            "How are you preparing for the CITS5508 Machine Learning exam since there is no cheat sheet allowed? "
            "Any tips appreciated. I am trying to focus on the main concepts, model assumptions, and how to explain "
            "evaluation metrics clearly."
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
            "how to map that idea properly. Are SQLAlchemy classes the Model, Jinja templates the View, "
            "and route functions the Controller?"
        ),
        category="Software Engineering",
        author=student,
    )

    thread_pca = ForumThread(
        title="I still do not really understand the idea behind PCA",
        body=(
            "I understand that PCA is used for dimensionality reduction, but I am still confused about the intuition. "
            "When we say PCA finds directions of maximum variance, does that mean it is finding the most important features?"
        ),
        category="AI & Data Science",
        author=qwang,
    )

    thread_flask = ForumThread(
        title="Best way to organise Flask routes for a group project?",
        body=(
            "Our project is getting bigger now, and I am wondering how we should organise routes, templates, "
            "models, and static files so that each feature stays manageable. Should each major feature have its "
            "own blueprint later?"
        ),
        category="Courses & Study Help",
        author=vraparla,
    )

    db.session.add_all([
        thread_exam,
        thread_mvc,
        thread_pca,
        thread_flask,
    ])
    db.session.flush()

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

    thread_flask.tags.extend([
        tags["cits5505"],
        tags["flask"],
        tags["web-development"],
    ])

    # Demo persisted likes/saves.
    thread_exam.liked_by.append(lecturer)
    thread_exam.liked_by.append(admin)
    thread_exam.saved_by.append(vraparla)

    thread_mvc.liked_by.append(lecturer)
    thread_mvc.saved_by.append(student)

    thread_pca.liked_by.append(student)
    thread_pca.liked_by.append(admin)
    thread_pca.saved_by.append(qwang)

    thread_flask.liked_by.append(student)
    thread_flask.liked_by.append(qwang)
    thread_flask.saved_by.append(lecturer)

    replies = [
        ForumReply(
            body=(
                "For the ML exam, focus on the core ideas first: what each model is trying to optimise, "
                "how to interpret the outputs, and why the evaluation metrics matter. Practising short written "
                "explanations will probably help more than memorising code."
            ),
            thread=thread_exam,
            author=lecturer,
        ),
        ForumReply(
            body=(
                "You are thinking about MVC in the right direction. In this Flask project, the SQLAlchemy classes "
                "are the Model because they represent database entities, the Jinja templates are the View because "
                "they define what the user sees, and the route functions act like the Controller because they receive "
                "requests, call the model, and choose which template to render."
            ),
            thread=thread_mvc,
            author=lecturer,
        ),
        ForumReply(
            body=(
                "A simple way to think about PCA is that it finds new directions through the data where the values "
                "vary the most. These directions are usually combinations of the original columns, not the original "
                "columns themselves."
            ),
            thread=thread_pca,
            author=lecturer,
        ),
        ForumReply(
            body=(
                "For now, keeping routes grouped clearly in routes.py is okay. If the project keeps growing, moving "
                "large features into separate blueprints would make the codebase easier to maintain."
            ),
            thread=thread_flask,
            author=admin,
        ),
    ]

    db.session.add_all(replies)
    db.session.commit()



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
        # Keep the central shared seed from app.seed.
        # This should create/reset the normal demo users and Study Buddy data.
        created_count = seed_demo_data(reset=True)

        # Ensure all team/demo users exist.
        student = get_or_create_user(
            username="hlionar",
            email="24661999@student.uwa.edu.au",
            password="passwd",
            role=User.ROLE_STUDENT,
            first_name="Hans",
            last_name="Lionar",
            uwa_id="24661999",
        )

        vraparla = get_or_create_user(
            username="vraparla",
            email="vraparla@cshub.local",
            password="passwd",
            role=User.ROLE_STUDENT,
            first_name="Varshitha",
            last_name="Raparla",
        )

        qwang = get_or_create_user(
            username="qwang",
            email="qwang@cshub.local",
            password="passwd",
            role=User.ROLE_STUDENT,
            first_name="Qiumei",
            last_name="Wang",
        )

        lecturer = get_or_create_user(
            username="MatthewDaggitt",
            email="matthew.daggitt@uwa.edu.au",
            password="passwd",
            role=User.ROLE_LECTURER,
            first_name="Matthew",
            last_name="Daggitt",
        )

        admin = get_or_create_user(
            username="admin",
            email="admin@cshub.local",
            password="admin",
            role=User.ROLE_ADMIN,
            first_name="Admin",
            last_name="User",
        )

        # Add forum demo content after the shared seed.
        clear_forum_data()
        tags = create_demo_forum_tags()
        create_demo_forum_data(student, lecturer, admin, vraparla, qwang, tags)

    print("Development database initialized.")
    print(f"Created {created_count} demo study sessions.")
    print("Forum demo data created.")
    print("Test users:")
    print("  hlionar / passwd")
    print("  vraparla / passwd")
    print("  qwang / passwd")
    print("  matthew.daggitt@uwa.edu.au / passwd")
    print("  admin / admin")

if __name__ == "__main__":
    seed_dev_db()