from app import db


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