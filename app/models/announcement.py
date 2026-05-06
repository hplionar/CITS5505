from app import db


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    slug = db.Column(db.String(120), unique=True, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    date_label = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    author = db.relationship("User", backref="announcements")

    @property
    def detail_items(self):
        return [line.strip() for line in self.details.splitlines() if line.strip()]
