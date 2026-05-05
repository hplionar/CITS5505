from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    if app.config.get("AUTO_CREATE_DATABASE", True):
        create_database_schema(app)
        if app.config.get("AUTO_SEED_DEMO_DATA", True):
            seed_empty_database(app)

    return app


def create_database_schema(app):
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
        ensure_study_session_location_column()


def ensure_study_session_location_column():
    inspector = inspect(db.engine)
    if "study_session" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("study_session")}
    if "location" not in columns:
        db.session.execute(text("ALTER TABLE study_session ADD COLUMN location VARCHAR(150)"))
        db.session.commit()


def seed_empty_database(app):
    with app.app_context():
        from app.seed import seed_demo_data

        seed_demo_data(reset=False)
