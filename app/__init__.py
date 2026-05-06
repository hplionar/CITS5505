from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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

    return app


def create_database_schema(app):
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
