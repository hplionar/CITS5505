from app import db


joined_sessions = db.Table(
    "joined_sessions",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("session_id", db.Integer, db.ForeignKey("study_session.id"), primary_key=True)
)


saved_sessions = db.Table(
    "saved_sessions",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("session_id", db.Integer, db.ForeignKey("study_session.id"), primary_key=True)
)