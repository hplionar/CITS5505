from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DB_PATH = INSTANCE_DIR / "studyhub.db"


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-before-submission"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DB_PATH.as_posix()}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prefer Flask-Migrate for team development:
    #   flask --app app:create_app db upgrade
    #   python scripts/seed_dev_db.py
    #
    # These legacy options should normally stay disabled.
    AUTO_CREATE_DATABASE = os.environ.get("AUTO_CREATE_DATABASE", "0") == "1"
    AUTO_SEED_DEMO_DATA = os.environ.get("AUTO_SEED_DEMO_DATA", "0") == "1"