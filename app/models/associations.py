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


liked_forum_threads = db.Table(
    "liked_forum_threads",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("thread_id", db.Integer, db.ForeignKey("forum_threads.id"), primary_key=True)
)


saved_forum_threads = db.Table(
    "saved_forum_threads",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("thread_id", db.Integer, db.ForeignKey("forum_threads.id"), primary_key=True)
)


forum_thread_tags = db.Table(
    "forum_thread_tags",
    db.Column("thread_id", db.Integer, db.ForeignKey("forum_threads.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("forum_tags.id"), primary_key=True)
)