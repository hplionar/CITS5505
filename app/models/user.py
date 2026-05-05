from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.associations import joined_sessions, saved_sessions


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
    study_hours = db.Column(db.Float, default=0)
    planned_leave_time = db.Column(db.String(50))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    hosted_sessions = db.relationship("StudySession", backref="host_user", lazy=True)
    joined = db.relationship("StudySession", secondary=joined_sessions, backref="joined_users")
    saved = db.relationship("StudySession", secondary=saved_sessions, backref="saved_users")

    @property
    def full_name(self):
        name_parts = [self.first_name, self.last_name]
        full_name = " ".join(part for part in name_parts if part)

        return full_name or self.username

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