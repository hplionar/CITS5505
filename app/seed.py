from app import db
from app.models import Announcement, SessionMessage, StudySession, User
from app.models.associations import joined_sessions, saved_sessions


def seed_demo_data(reset=False):
    if reset:
        reset_demo_data()
    elif StudySession.query.count() > 0:
        ensure_demo_announcements()
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

    varshitha = User.query.filter_by(username="vraparla").first()
    if varshitha is None:
        varshitha = User(
            first_name="Varshitha",
            last_name="Raparla",
            username="vraparla",
            email="24700839@student.uwa.edu.au",
            uwa_id="24700839",
            role=User.ROLE_STUDENT,
        )
        varshitha.set_password("passwd")

    qiumei = User.query.filter_by(username="qwang").first()
    if qiumei is None:
        qiumei = User(
            first_name="Qiumei",
            last_name="Wang",
            username="qwang",
            email="24570238@student.uwa.edu.au",
            uwa_id="24570238",
            role=User.ROLE_STUDENT,
        )
        qiumei.set_password("passwd")

    db.session.add_all([student, lecturer, admin, varshitha, qiumei])
    db.session.commit()

    demo_sessions = build_demo_sessions(student, lecturer, admin, varshitha, qiumei)
    db.session.add_all(demo_sessions)
    db.session.add_all(build_demo_announcements(admin, lecturer))
    db.session.commit()

    student.joined.extend([demo_sessions[0], demo_sessions[2], demo_sessions[4]])
    lecturer.joined.extend([demo_sessions[1], demo_sessions[5]])
    admin.joined.append(demo_sessions[3])
    varshitha.joined.extend([demo_sessions[0], demo_sessions[3]])
    qiumei.joined.extend([demo_sessions[1], demo_sessions[4]])

    student.saved.extend([demo_sessions[1], demo_sessions[5]])
    lecturer.saved.append(demo_sessions[4])
    admin.saved.append(demo_sessions[0])
    varshitha.saved.append(demo_sessions[2])
    qiumei.saved.append(demo_sessions[5])
    db.session.commit()

    return len(demo_sessions)


def reset_demo_data():
    db.session.execute(joined_sessions.delete())
    db.session.execute(saved_sessions.delete())
    Announcement.query.delete()
    SessionMessage.query.delete()
    StudySession.query.delete()
    User.query.delete()
    db.session.commit()


def ensure_demo_announcements():
    admin = User.query.filter_by(username="admin").first()
    lecturer = User.query.filter_by(username="MatthewDaggitt").first()

    if admin is None or lecturer is None:
        return

    existing_slugs = {
        announcement.slug
        for announcement in Announcement.query.with_entities(Announcement.slug).all()
    }

    new_announcements = [
        announcement
        for announcement in build_demo_announcements(admin, lecturer)
        if announcement.slug not in existing_slugs
    ]

    if new_announcements:
        db.session.add_all(new_announcements)
        db.session.commit()


def build_demo_sessions(student, lecturer, admin, varshitha, qiumei):
    return [
        StudySession(
            unit_code="CITS5508",
            topic="Machine Learning Revision Group",
            description="Review supervised learning, model evaluation, and common exam-style machine learning questions.",
            host_name=varshitha.full_name,
            day="Mon",
            time="10:00 AM",
            mode="online",
            location=None,
            capacity=6,
            joined_count=2,
            host_id=varshitha.id,
        ),
        StudySession(
            unit_code="CITS5505",
            topic="Agile Web Development Sprint",
            description="Work through Flask routes, SQLAlchemy models, Jinja templates, testing, and final project polish.",
            host_name=qiumei.full_name,
            day="Tue",
            time="2:00 PM",
            mode="hybrid",
            location="EZONE Central 2.03",
            capacity=8,
            joined_count=1,
            host_id=qiumei.id,
        ),
        StudySession(
            unit_code="CITS5504",
            topic="Data Warehousing Study Session",
            description="Revise data warehouse design, dimensional modelling, ETL concepts, and analytics workflows.",
            host_name=student.full_name,
            day="Wed",
            time="4:30 PM",
            mode="in-person",
            location="CSSE: [G09]Computer Lab",
            capacity=5,
            joined_count=2,
            host_id=student.id,
        ),
        StudySession(
            unit_code="CITS4401",
            topic="Software Requirements and Design Workshop",
            description="Compare use cases, acceptance criteria, architecture decisions, and UI flow diagrams.",
            host_name=varshitha.full_name,
            day="Thu",
            time="11:00 AM",
            mode="online",
            location=None,
            capacity=4,
            joined_count=1,
            host_id=varshitha.id,
        ),
        StudySession(
            unit_code="CITS4404",
            topic="Artificial Intelligence Problem Solving",
            description="Practise search strategies, knowledge representation, and reasoning problems with classmates.",
            host_name=qiumei.full_name,
            day="Fri",
            time="3:00 PM",
            mode="hybrid",
            location="EZONE North 1.24",
            capacity=6,
            joined_count=2,
            host_id=qiumei.id,
        ),
        StudySession(
            unit_code="CITS4403",
            topic="Computational Modelling Review",
            description="Discuss modelling assumptions, simulation results, and how to explain computational experiments clearly.",
            host_name=lecturer.full_name,
            day="Sat",
            time="1:00 PM",
            mode="online",
            location=None,
            capacity=5,
            joined_count=1,
            host_id=lecturer.id,
        ),
    ]


def build_demo_announcements(admin, lecturer):
    return [
        Announcement(
            slug="machine-learning-databricks-workshop",
            category="Event",
            date_label="This week",
            title="Machine Learning on Databricks workshop",
            body="The UWA Data Science Club is hosting a hands-on workshop for students interested in end-to-end machine learning workflows.",
            details=(
                "Hands-on introduction to building machine learning workflows with Databricks.\n"
                "Suitable for students revising machine learning, data engineering, or cloud-native analytics topics.\n"
                "Bring your laptop and UWA account details if you want to follow along with the workshop activities."
            ),
            author_id=admin.id,
        ),
        Announcement(
            slug="scheduled-server-maintenance",
            category="Maintenance",
            date_label="Friday evening",
            title="Scheduled server maintenance",
            body="CSHub may be briefly unavailable while routine maintenance is completed. Please save any draft posts before the maintenance window.",
            details=(
                "The maintenance window is expected to be short.\n"
                "Study Buddy sessions and discussion posts should remain available after the update.\n"
                "Users should avoid submitting long posts during the maintenance period."
            ),
            author_id=admin.id,
        ),
        Announcement(
            slug="study-buddy-exam-revision",
            category="Study",
            date_label="Week 10",
            title="Study Buddy exam revision sessions",
            body="Students are encouraged to create or join revision sessions for CITS units before the final assessment period.",
            details=(
                "Create sessions for units such as CITS5505, CITS5508, CITS4404, and CITS4403.\n"
                "Use online, in-person, or hybrid mode depending on how your group wants to meet.\n"
                "Keep session descriptions clear so other students can find relevant revision groups."
            ),
            author_id=lecturer.id,
        ),
    ]
