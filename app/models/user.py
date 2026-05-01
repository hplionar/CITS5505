from app import db
from app.models.associations import joined_sessions, saved_sessions


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)

    avatar_url = db.Column(db.String(255))
    study_hours = db.Column(db.Float, default=0)
    planned_leave_time = db.Column(db.String(50))

    hosted_sessions = db.relationship("StudySession", backref="host_user", lazy=True)
    joined = db.relationship("StudySession", secondary=joined_sessions, backref="joined_users")
    saved = db.relationship("StudySession", secondary=saved_sessions, backref="saved_users")