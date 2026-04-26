from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "app" / "templates"),
    static_folder=str(BASE_DIR / "app" / "static"),
    static_url_path="/static"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studyhub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Association table: joined sessions
joined_sessions = db.Table(
    "joined_sessions",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("session_id", db.Integer, db.ForeignKey("study_session.id"), primary_key=True)
)

# Association table: saved sessions
saved_sessions = db.Table(
    "saved_sessions",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("session_id", db.Integer, db.ForeignKey("study_session.id"), primary_key=True)
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    study_hours = db.Column(db.Float, default=0)
    planned_leave_time = db.Column(db.String(50), nullable=True)

    hosted_sessions = db.relationship("StudySession", backref="host_user", lazy=True)
    joined = db.relationship("StudySession", secondary=joined_sessions, backref="joined_users")
    saved = db.relationship("StudySession", secondary=saved_sessions, backref="saved_users")


class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(120), nullable=False)
    topic = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    host_name = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    joined_count = db.Column(db.Integer, default=1)

    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class SessionMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(db.Integer, db.ForeignKey("study_session.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("session_message.id"), nullable=True)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    session = db.relationship("StudySession", backref="messages")
    user = db.relationship("User", backref="messages")

    replies = db.relationship(
        "SessionMessage",
        backref=db.backref("parent", remote_side=[id])
    )


def get_current_user():
    """
    Temporary helper for Checkpoint 3.
    Hardcode one demo user first.
    """
    user = User.query.get(1)
    if not user:
        user = User(id=1, username="Meryl")
        db.session.add(user)
        db.session.commit()
    return user


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("studybuddy"))

    return render_template("auth/login.html")

@app.route("/")
def home():
    return redirect(url_for("studybuddy"))


@app.route("/studybuddy")
def studybuddy():
    sessions = StudySession.query.order_by(StudySession.id.desc()).all()
    current_user = get_current_user()

    joined_ids = {session.id for session in current_user.joined}
    saved_ids = {session.id for session in current_user.saved}
    hosted_ids = {session.id for session in current_user.hosted_sessions}

    return render_template(
        "studybuddy.html",
        sessions=sessions,
        joined_ids=joined_ids,
        saved_ids=saved_ids,
        hosted_ids=hosted_ids
    )


@app.route("/studybuddy/create", methods=["POST"])
def create_session():
    current_user = get_current_user()

    unit_code = request.form.get("unit_code", "").strip()
    topic = request.form.get("topic", "").strip()
    description = request.form.get("description", "").strip()
    host_name = request.form.get("host_name", "").strip()
    day = request.form.get("day", "").strip()
    time = request.form.get("time", "").strip()
    mode = request.form.get("mode", "").strip()
    capacity_raw = request.form.get("capacity", "").strip()

    # Basic validation
    if not all([unit_code, topic, description, host_name, day, time, mode, capacity_raw]):
        return redirect(url_for("studybuddy"))

    try:
        capacity = int(capacity_raw)
    except ValueError:
        return redirect(url_for("studybuddy"))

    if capacity < 2:
        return redirect(url_for("studybuddy"))

    new_session = StudySession(
        unit_code=unit_code.upper(),
        topic=topic,
        description=description,
        host_name=host_name,
        day=day,
        time=time,
        mode=mode,
        capacity=capacity,
        joined_count=1,
        host_id=current_user.id
    )

    db.session.add(new_session)
    db.session.commit()

    # Host automatically joins their own session
    if new_session not in current_user.joined:
        current_user.joined.append(new_session)
        db.session.commit()

    return redirect(url_for("studybuddy"))


@app.route("/sessions/<int:session_id>/join", methods=["POST"])
def join_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session not in current_user.joined and session.joined_count < session.capacity:
        current_user.joined.append(session)
        session.joined_count += 1
        db.session.commit()

    return redirect(url_for("session_detail", session_id=session.id))


@app.route("/sessions/<int:session_id>/leave", methods=["POST"])
def leave_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session in current_user.joined:
        current_user.joined.remove(session)
        session.joined_count = max(0, session.joined_count - 1)
        db.session.commit()

    return redirect(url_for("my_sessions", view="joined"))


@app.route("/sessions/<int:session_id>/save", methods=["POST"])
def save_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session not in current_user.saved:
        current_user.saved.append(session)
        db.session.commit()

    return redirect(url_for("studybuddy"))


@app.route("/sessions/<int:session_id>/unsave", methods=["POST"])
def unsave_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session in current_user.saved:
        current_user.saved.remove(session)
        db.session.commit()

    return redirect(url_for("my_sessions", view="saved"))


@app.route("/my-sessions")
def my_sessions():
    current_user = get_current_user()
    view = request.args.get("view", "all")

    if view == "joined":
        sessions = current_user.joined
    elif view == "saved":
        sessions = current_user.saved
    elif view == "hosted":
        sessions = current_user.hosted_sessions
    else:
        joined_ids = {s.id for s in current_user.joined}
        saved_ids = {s.id for s in current_user.saved}
        hosted_ids = {s.id for s in current_user.hosted_sessions}
        all_ids = joined_ids | saved_ids | hosted_ids

        if all_ids:
            sessions = StudySession.query.filter(StudySession.id.in_(all_ids)).all()
        else:
            sessions = []

    return render_template(
        "my_sessions.html",
        sessions=sessions,
        current_view=view
    )


@app.route("/init-db")
def init_db():
    db.create_all()

    current_user = get_current_user()

    if StudySession.query.count() == 0:
        demo_sessions = [
            StudySession(
                unit_code="CITS4401 • REQUIREMENTS & DESIGN",
                topic="Exam Revision Group",
                description="Looking for 2–3 people to revise functional and non-functional requirements together.",
                host_name="Qiumei W.",
                day="Tue",
                time="4:00 PM",
                mode="in-person",
                capacity=5,
                joined_count=3,
                host_id=current_user.id
            ),
            StudySession(
                unit_code="PYTHON • DEBUGGING PRACTICE",
                topic="Loop and Indexing Help",
                description="Small online session to practice debugging common beginner mistakes in Python code.",
                host_name="Varshitha R.",
                day="Wed",
                time="7:00 PM",
                mode="online",
                capacity=4,
                joined_count=2,
                host_id=current_user.id
            ),
            StudySession(
                unit_code="WEB DEVELOPMENT • HTML/CSS",
                topic="Beginner Study Buddy",
                description="Weekly casual meetup for students learning HTML, CSS, and JavaScript fundamentals.",
                host_name="Matthew",
                day="Thu",
                time="5:30 PM",
                mode="hybrid",
                capacity=6,
                joined_count=4,
                host_id=current_user.id
            )
        ]

        db.session.add_all(demo_sessions)
        db.session.commit()

    return "Database initialized successfully."

@app.route("/sessions/<int:session_id>")
def session_detail(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    messages = SessionMessage.query.filter_by(
        session_id=session.id,
        parent_id=None
    ).order_by(SessionMessage.created_at.desc()).all()

    joined_ids = {user.id for user in session.joined_users}
    is_joined = current_user.id in joined_ids

    return render_template(
        "session_detail.html",
        session=session,
        messages=messages,
        current_user=current_user,
        is_joined=is_joined
    )


@app.route("/sessions/<int:session_id>/messages", methods=["POST"])
def add_message(session_id):
    current_user = get_current_user()
    content = request.form.get("content", "").strip()

    if content:
        message = SessionMessage(
            session_id=session_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(message)
        db.session.commit()

    return redirect(url_for("session_detail", session_id=session_id))


@app.route("/sessions/<int:session_id>/messages/<int:message_id>/reply", methods=["POST"])
def reply_message(session_id, message_id):
    current_user = get_current_user()
    content = request.form.get("content", "").strip()

    if content:
        reply = SessionMessage(
            session_id=session_id,
            user_id=current_user.id,
            parent_id=message_id,
            content=content
        )
        db.session.add(reply)
        db.session.commit()

    return redirect(url_for("session_detail", session_id=session_id))

@app.route("/test-base")
def test_base():
    return render_template("test_base.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(debug=True)