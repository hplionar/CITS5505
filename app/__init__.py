from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from flask_wtf.csrf import CSRFProtect
from config import Config


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    csrf.init_app(app)

    # Import models so Flask-Migrate/Alembic can detect model changes.
    from app import models  # noqa: F401

    from app.routes import main
    app.register_blueprint(main)

    # Legacy fallback only.
    # For team development, prefer:
    #   flask db upgrade
    #   python scripts/seed_dev_db.py
    #
    # This should normally be False when using migrations.
    if app.config.get("AUTO_CREATE_DATABASE", False):
        create_database_schema(app)

        if app.config.get("AUTO_SEED_DEMO_DATA", False):
            seed_empty_database(app)

    return app


def create_database_schema(app):
    """
    Legacy helper for creating tables without migrations.

    Prefer Flask-Migrate instead:
        flask db upgrade

    This function is kept only as a fallback for local development.
    """
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
        ensure_study_session_columns()


def ensure_study_session_columns():
    """
    Legacy helper for old local databases.

    These manual ALTER TABLE statements should eventually be replaced
    by proper migration files.
    """
    inspector = inspect(db.engine)

    if "study_session" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("study_session")
    }

    if "location" not in columns:
        db.session.execute(
            text("ALTER TABLE study_session ADD COLUMN location VARCHAR(150)")
        )
        db.session.commit()

    if "session_date" not in columns:
        db.session.execute(
            text("ALTER TABLE study_session ADD COLUMN session_date DATE")
        )
        db.session.commit()


def seed_empty_database(app):
    """
    Legacy helper for auto-seeding an empty database.

    Prefer running this manually:
        python scripts/seed_dev_db.py
    """
    with app.app_context():
        from app.seed import seed_demo_data

        seed_demo_data(reset=False)