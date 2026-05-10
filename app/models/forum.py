from app import db
from app.models.associations import liked_forum_threads, saved_forum_threads


class ForumThread(db.Model):
    __tablename__ = "forum_threads"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General")

    # Comma-separated tags for now, e.g. "mvc,flask,web-development".
    # This keeps the implementation simple for the deadline.
    tags = db.Column(db.String(255), nullable=True)

    is_pinned = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False
    )

    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    author = db.relationship(
        "User",
        back_populates="forum_threads"
    )

    replies = db.relationship(
        "ForumReply",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy=True
    )

    liked_by = db.relationship(
        "User",
        secondary=liked_forum_threads,
        back_populates="liked_forum_threads"
    )

    saved_by = db.relationship(
        "User",
        secondary=saved_forum_threads,
        back_populates="saved_forum_threads"
    )

    @property
    def reply_count(self):
        return len(self.replies)

    @property
    def like_count(self):
        return len(self.liked_by)

    @property
    def tag_list(self):
        if not self.tags:
            return []

        return [
            tag.strip()
            for tag in self.tags.split(",")
            if tag.strip()
        ]

    def __repr__(self):
        return f"<ForumThread {self.title}>"


class ForumReply(db.Model):
    __tablename__ = "forum_replies"

    id = db.Column(db.Integer, primary_key=True)

    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    thread_id = db.Column(
        db.Integer,
        db.ForeignKey("forum_threads.id"),
        nullable=False
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    thread = db.relationship(
        "ForumThread",
        back_populates="replies"
    )

    author = db.relationship(
        "User",
        back_populates="forum_replies"
    )

    def __repr__(self):
        return f"<ForumReply thread_id={self.thread_id}>"