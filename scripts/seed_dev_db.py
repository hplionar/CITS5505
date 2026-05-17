from datetime import datetime, timedelta
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
    """Create forum tags for demo threads."""
    tags = {
        "study-tips": ForumTag(name="Study Tips", slug="study-tips"),
        "cits5505": ForumTag(name="CITS5505", slug="cits5505"),
        "exam-prep": ForumTag(name="Exam Prep", slug="exam-prep"),
        "mvc": ForumTag(name="MVC", slug="mvc"),
        "flask": ForumTag(name="Flask", slug="flask"),
        "selenium": ForumTag(name="Selenium", slug="selenium"),
        "testing": ForumTag(name="Testing", slug="testing"),
        "web-development": ForumTag(name="Web Development", slug="web-development"),
        "machine-learning": ForumTag(name="Machine Learning", slug="machine-learning"),
        "pca": ForumTag(name="PCA", slug="pca"),
        "intuition": ForumTag(name="Intuition", slug="intuition"),
        "python": ForumTag(name="Python", slug="python"),
        "cybersecurity": ForumTag(name="Cybersecurity", slug="cybersecurity"),
        "security": ForumTag(name="Security", slug="security"),
        "ctf": ForumTag(name="CTF", slug="ctf"),
    }

    db.session.add_all(tags.values())
    db.session.commit()

    return tags


def add_tags(thread, tags, tag_slugs):
    """Attach existing tag objects to a thread."""
    for slug in tag_slugs:
        if slug in tags and tags[slug] not in thread.tags:
            thread.tags.append(tags[slug])


def create_thread(
    title,
    body,
    category,
    author,
    tags,
    tag_slugs,
    created_at,
    is_pinned=False,
):
    """Create a forum thread with consistent demo timestamps and tags."""
    thread = ForumThread(
        title=title,
        body=body,
        category=category,
        author=author,
        is_pinned=is_pinned,
        created_at=created_at,
        updated_at=created_at,
    )

    db.session.add(thread)
    db.session.flush()

    add_tags(thread, tags, tag_slugs)

    return thread


def add_thread_activity(thread, users, index):
    """Add varied likes and saves so popular sorting has useful demo data."""
    like_count = index % 5

    for user in users[:like_count]:
        if user not in thread.liked_by:
            thread.liked_by.append(user)

    if index % 6 == 0:
        thread.saved_by.append(users[0])
    elif index % 9 == 0:
        thread.saved_by.append(users[-1])


def create_dummy_forum_threads(student, lecturer, admin, vraparla, qwang, tags):
    """Create simple numbered dummy forum threads for testing infinite scroll."""
    now = datetime.utcnow()

    authors = [student, vraparla, qwang, lecturer, admin]
    activity_users = [lecturer, admin, qwang, vraparla, student]

    dummy_groups = [
        {
            "category": "Web Development",
            "prefix": "Web Development",
            "count": 20,
            "tag_slugs": ["cits5505", "flask", "web-development"],
            "body": (
                "This is a dummy Web Development discussion used to test the forum feed, "
                "category filtering, sorting, and infinite scroll behaviour."
            ),
        },
        {
            "category": "AI & Data Science",
            "prefix": "AI & Data Science",
            "count": 12,
            "tag_slugs": ["machine-learning", "python", "intuition"],
            "body": (
                "This is a dummy AI & Data Science discussion used to test the forum feed, "
                "category filtering, sorting, and infinite scroll behaviour."
            ),
        },
        {
            "category": "Cybersecurity",
            "prefix": "Cybersecurity",
            "count": 10,
            "tag_slugs": ["cybersecurity", "security", "ctf"],
            "body": (
                "This is a dummy Cybersecurity discussion used to test the forum feed, "
                "category filtering, sorting, and infinite scroll behaviour."
            ),
        },
        {
            "category": "General",
            "prefix": "General",
            "count": 8,
            "tag_slugs": ["study-tips", "exam-prep"],
            "body": (
                "This is a dummy General discussion used to test the forum feed, "
                "category filtering, sorting, and infinite scroll behaviour."
            ),
        },
    ]

    dummy_index = 1

    for group in dummy_groups:
        for number in range(1, group["count"] + 1):
            author = authors[(dummy_index - 1) % len(authors)]
            created_at = now - timedelta(hours=dummy_index + 4)

            thread = create_thread(
                title=f"{group['prefix']} {number}",
                body=group["body"],
                category=group["category"],
                author=author,
                tags=tags,
                tag_slugs=group["tag_slugs"],
                created_at=created_at,
            )

            add_thread_activity(thread, activity_users, dummy_index)

            dummy_index += 1


def create_demo_forum_data(student, lecturer, admin, vraparla, qwang, tags):
    """Create demo forum threads, tags, likes, saves, and replies."""
    now = datetime.utcnow()

    thread_exam = create_thread(
        title="How are you preparing for the CITS5508 Machine Learning exam?",
        body=(
            "How are you preparing for the CITS5508 Machine Learning exam since there is no cheat sheet allowed? "
            "Any tips appreciated. I am trying to focus on the main concepts, model assumptions, and how to explain "
            "evaluation metrics clearly."
        ),
        category="General",
        author=student,
        tags=tags,
        tag_slugs=["study-tips", "machine-learning", "exam-prep"],
        created_at=now - timedelta(hours=1),
    )

    thread_mvc = create_thread(
        title="I still do not really understand Model-View-Controller",
        body=(
            "I keep seeing Model-View-Controller explained as Model for data, View for UI, "
            "and Controller for application logic. But in our actual Flask project, I am not sure "
            "how to map that idea properly. Are SQLAlchemy classes the Model, Jinja templates the View, "
            "and route functions the Controller?"
        ),
        category="Web Development",
        author=student,
        tags=tags,
        tag_slugs=["cits5505", "mvc", "web-development"],
        created_at=now - timedelta(hours=2),
    )

    thread_pca = create_thread(
        title="I still do not really understand the idea behind PCA",
        body=(
            "I understand that PCA is used for dimensionality reduction, but I am still confused about the intuition. "
            "When we say PCA finds directions of maximum variance, does that mean it is finding the most important features?"
        ),
        category="AI & Data Science",
        author=qwang,
        tags=tags,
        tag_slugs=["machine-learning", "pca", "intuition"],
        created_at=now - timedelta(hours=3),
    )

    thread_selenium = create_thread(
        title="What is Selenium testing and are there any good resources to read?",
        body=(
            "I have seen Selenium mentioned for testing web applications, but I am still not fully sure what it does. "
            "Is it mainly used to check whether buttons, forms, login, and page navigation work in the browser? "
            "Does anyone know a good beginner-friendly resource before we write Selenium tests for our Flask project?"
        ),
        category="Web Development",
        author=vraparla,
        tags=tags,
        tag_slugs=["cits5505", "selenium", "web-development"],
        created_at=now - timedelta(hours=4),
    )

    # Demo thread likes and saves.
    # Note: comment likes are not seeded because the app currently supports
    # likes on forum threads, not individual replies.
    thread_exam.liked_by.extend([lecturer, admin])
    thread_exam.saved_by.append(vraparla)

    thread_mvc.liked_by.extend([lecturer, admin, qwang, vraparla])
    thread_mvc.saved_by.append(student)

    thread_pca.liked_by.extend([student, admin])
    thread_pca.saved_by.append(qwang)

    thread_selenium.liked_by.extend([student, qwang])
    thread_selenium.saved_by.append(lecturer)

    # Top-level replies for regular demo threads.
    exam_reply = ForumReply(
        body=(
            "For the ML exam, focus on the core ideas first: what each model is trying to optimise, "
            "how to interpret the outputs, and why the evaluation metrics matter. Practising short written "
            "explanations will probably help more than memorising code."
        ),
        thread=thread_exam,
        author=lecturer,
        created_at=now - timedelta(minutes=45),
    )

    pca_reply = ForumReply(
        body=(
            "A simple way to think about PCA is that it finds new directions through the data where the values "
            "vary the most. These directions are usually combinations of the original columns, not the original "
            "columns themselves."
        ),
        thread=thread_pca,
        author=lecturer,
        created_at=now - timedelta(hours=2, minutes=30),
    )

    selenium_reply = ForumReply(
        body=(
            "Yes, Selenium is mainly useful for testing how the app behaves in a real browser. "
            "For example, it can check login, form submission, button clicks, page navigation, and whether expected "
            "content appears after an action. I found this introduction helpful: "
            "https://www.geeksforgeeks.org/software-engineering/software-engineering-selenium-an-automation-tool/"
        ),
        thread=thread_selenium,
        author=qwang,
        created_at=now - timedelta(hours=3, minutes=30),
    )

    db.session.add_all([
        exam_reply,
        pca_reply,
        selenium_reply,
    ])

    # MVC demo reply tree.
    # This thread intentionally has nested replies so the thread detail page
    # clearly demonstrates the branch UI.
    matthew_mvc_answer = ForumReply(
        body=(
            "You are thinking about MVC in the right direction. In this Flask project, the SQLAlchemy classes "
            "are the Model because they represent database entities, the Jinja templates are the View because "
            "they define what the user sees, and the route functions act like the Controller because they receive "
            "requests, call the model, and choose which template to render."
        ),
        thread=thread_mvc,
        author=lecturer,
        created_at=now - timedelta(hours=1, minutes=40),
    )

    db.session.add(matthew_mvc_answer)
    db.session.flush()

    hans_mvc_reply = ForumReply(
        body="Thanks for explaining this.",
        thread=thread_mvc,
        author=student,
        parent=matthew_mvc_answer,
        created_at=now - timedelta(hours=1, minutes=20),
    )

    db.session.add(hans_mvc_reply)
    db.session.flush()

    qiumei_mvc_reply = ForumReply(
        body=(
            "That makes sense now. I also found this YouTube video about MVC in Python/Flask helpful too: "
            "https://www.youtube.com/watch?v=RFPEz2Jwh-U"
        ),
        thread=thread_mvc,
        author=qwang,
        parent=hans_mvc_reply,
        created_at=now - timedelta(hours=1),
    )

    db.session.add(qiumei_mvc_reply)
    db.session.flush()

    varshitha_mvc_reply = ForumReply(
        body="Cool video.",
        thread=thread_mvc,
        author=vraparla,
        parent=qiumei_mvc_reply,
        created_at=now - timedelta(minutes=45),
    )

    extra_mvc_comment = ForumReply(
        body=(
            "I think my confusion came from trying to match MVC too literally. In our project, it seems more useful "
            "to think of models.py as the database layer, the templates as the pages users see, and routes.py as the "
            "place where the request is handled and connected to the right data."
        ),
        thread=thread_mvc,
        author=student,
        created_at=now - timedelta(minutes=30),
    )

    db.session.add_all([
        varshitha_mvc_reply,
        extra_mvc_comment,
    ])

    # Simple numbered dummy forum content for category filters, sorting, and infinite scroll.
    create_dummy_forum_threads(student, lecturer, admin, vraparla, qwang, tags)

    db.session.commit()


def seed_dev_db():
    app = create_app()

    with app.app_context():
        # Keep the central shared seed from app.seed.
        # This creates/resets the normal demo users and Study Buddy data.
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

        forum_thread_count = ForumThread.query.count()

    print("Development database initialized.")
    print(f"Created {created_count} demo study sessions.")
    print(f"Forum demo data created with {forum_thread_count} threads.")
    print("Test users:")
    print("  hlionar / passwd")
    print("  vraparla / passwd")
    print("  qwang / passwd")
    print("  matthew.daggitt@uwa.edu.au / passwd")
    print("  admin / admin")


if __name__ == "__main__":
    seed_dev_db()