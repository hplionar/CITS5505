from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///studyhub.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False