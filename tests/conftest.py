import os
import socket
import sys
import tempfile
import threading
from contextlib import closing
from pathlib import Path

import pytest
from werkzeug.serving import make_server

ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_DB = Path(tempfile.gettempdir()) / "cits5505_test_studyhub.db"
sys.path.insert(0, str(ROOT_DIR))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key"

from app import create_app, db
from app.models import StudySession, User


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
        yield flask_app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client):
    login(client)
    return client


def seed_database():
    student = User(
        username="student",
        email="student@example.com",
        first_name="Study",
        last_name="Student",
        role=User.ROLE_STUDENT,
    )
    student.set_password("Password1")

    host = User(
        username="host",
        email="host@example.com",
        first_name="Session",
        last_name="Host",
        role=User.ROLE_STUDENT,
    )
    host.set_password("Password1")

    db.session.add_all([student, host])
    db.session.commit()

    session = StudySession(
        unit_code="CITS5505",
        topic="Seeded Study Session",
        description="A seeded study session for tests.",
        host_name=host.full_name,
        day="Fri",
        time="4:00 PM",
        mode="online",
        location=None,
        capacity=5,
        joined_count=1,
        host_id=host.id,
    )
    db.session.add(session)
    db.session.commit()
    host.joined.append(session)
    db.session.commit()


def login(client, identifier="student", password="Password1"):
    return client.post(
        "/login",
        data={"identifier": identifier, "password": password},
        follow_redirects=True,
    )


@pytest.fixture
def live_server(app):
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def browser():
    selenium = pytest.importorskip("selenium")
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")

    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome WebDriver is not available: {exc}")

    driver.implicitly_wait(2)
    yield driver
    driver.quit()


def _free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
