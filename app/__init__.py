from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config


db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

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


def seed_empty_database(app):
    """
    Legacy helper for auto-seeding an empty database.

    Prefer running this manually:
        python scripts/seed_dev_db.py
    """
    with app.app_context():
        from app.seed import seed_demo_data

        seed_demo_data(reset=False)
