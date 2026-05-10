from app import db
from app.models.associations import (
    liked_forum_threads,
    saved_forum_threads,
    forum_thread_tags,
)


class ForumTag(db.Model):
    __tablename__ = "forum_tags"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    threads = db.relationship(
        "ForumThread",
        secondary=forum_thread_tags,
        back_populates="tags"
    )

    def __repr__(self):
        return f"<ForumTag {self.slug}>"


class ForumThread(db.Model):
    __tablename__ = "forum_threads"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General")

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

    tags = db.relationship(
        "ForumTag",
        secondary=forum_thread_tags,
        back_populates="threads"
    )

    @property
    def reply_count(self):
        return len(self.replies)

    @property
    def like_count(self):
        return len(self.liked_by)

    @property
    def tag_list(self):
        return [
            tag.slug
            for tag in self.tags
            if tag.is_active
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