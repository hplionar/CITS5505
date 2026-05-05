from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.seed import seed_demo_data


def seed_dev_db():
    app = create_app()

    with app.app_context():
        created_count = seed_demo_data(reset=True)

    print("Development database initialized.")
    print(f"Created {created_count} demo study sessions.")
    print("Test users:")
    print("  hlionar / passwd")
    print("  matthew.daggitt@uwa.edu.au / passwd")
    print("  admin / admin")


if __name__ == "__main__":
    seed_dev_db()
