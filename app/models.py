from app import db

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

    avatar_url = db.Column(db.String(255))
    study_hours = db.Column(db.Float, default=0)
    planned_leave_time = db.Column(db.String(50))

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
    parent_id = db.Column(db.Integer, db.ForeignKey("session_message.id"))

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    session = db.relationship("StudySession", backref="messages")
    user = db.relationship("User", backref="messages")

    replies = db.relationship(
        "SessionMessage",
        backref=db.backref("parent", remote_side=[id])
    )