from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.associations import (
    joined_sessions,
    saved_sessions,
    liked_forum_threads as liked_forum_threads_table,
    saved_forum_threads as saved_forum_threads_table,
)


class User(db.Model):
    ROLE_STUDENT = "student"
    ROLE_LECTURER = "lecturer"
    ROLE_ADMIN = "admin"

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Optional because lecturers/admins may not have a student ID.
    uwa_id = db.Column(db.String(20), unique=True, nullable=True)

    role = db.Column(db.String(20), nullable=False, default=ROLE_STUDENT)

    password_hash = db.Column(db.String(255), nullable=False)

    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    study_hours = db.Column(db.Float, default=0)
    planned_leave_time = db.Column(db.String(50))

    notify_study_messages = db.Column(db.Boolean, nullable=False, default=True)
    notify_session_reminders = db.Column(db.Boolean, nullable=False, default=True)
    notify_announcements = db.Column(db.Boolean, nullable=False, default=True)

    preferred_study_mode = db.Column(db.String(20), nullable=True)
    preferred_location = db.Column(db.String(150), nullable=True)
    interested_units = db.Column(db.String(255), nullable=True)

    show_full_name = db.Column(db.Boolean, nullable=False, default=True)
    show_joined_sessions = db.Column(db.Boolean, nullable=False, default=False)
    show_saved_sessions = db.Column(db.Boolean, nullable=False, default=False)
    allow_profile_discovery = db.Column(db.Boolean, nullable=False, default=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    hosted_sessions = db.relationship("StudySession", backref="host_user", lazy=True)
    joined = db.relationship("StudySession", secondary=joined_sessions, backref="joined_users")
    saved = db.relationship("StudySession", secondary=saved_sessions, backref="saved_users")

    forum_threads = db.relationship("ForumThread", back_populates="author", lazy=True)
    forum_replies = db.relationship("ForumReply", back_populates="author", lazy=True)

    liked_forum_threads = db.relationship(
        "ForumThread",
        secondary=liked_forum_threads_table,
        back_populates="liked_by"
    )

    saved_forum_threads = db.relationship(
        "ForumThread",
        secondary=saved_forum_threads_table,
        back_populates="saved_by"
    )

    @property
    def full_name(self):
        name_parts = [self.first_name, self.last_name]
        full_name = " ".join(part for part in name_parts if part)

        return full_name or self.username

    @property
    def display_name(self):
        if self.show_full_name:
            return self.full_name

        return self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_lecturer(self):
        return self.role == self.ROLE_LECTURER

    def __repr__(self):
        return f"<User {self.username}>"
