# CSHub

CSHub is a Flask-based web application designed for UWA Computer Science and Software Engineering students to communicate, share information, and organise study activities in one place. The application combines a community forum, announcements, Study Buddy sessions, user profiles, notifications, search, and saved content so that students can find useful information and interact with other users.

The purpose of CSHub is to support peer learning and student collaboration. Instead of separating questions, study planning, announcements, and saved resources across different tools, CSHub provides a single student-focused hub where users can ask questions, reply to discussions, join study sessions, and view activity from other students.

## Design and Use

CSHub is designed to be:

- **Engaging:** the interface uses a clean layout, dark visual style, clear cards, icons, and focused navigation to make important actions easy to notice.
- **Effective:** the application gives students practical value by supporting discussion, peer help, search, study-session organisation, announcements, notifications, and saved resources.
- **Intuitive:** common actions such as creating posts, replying to threads, searching, joining sessions, saving content, and viewing profiles are available through clear navigation and consistent UI patterns.

Users can register and log in, create forum posts, comment on discussions, like and save forum threads, search for content, join or save Study Buddy sessions, receive session message notifications, and view profile activity. User data is persisted between sessions using a SQLite database managed through SQLAlchemy and Flask-Migrate.

## Features

- User registration, login, and logout
- Passwords stored securely using hashed passwords
- CSRF protection on forms
- Forum threads and replies
- Thread likes and saved forum posts
- Study Buddy sessions
- Join and save study sessions
- Session message notifications
- User profile page with activity statistics
- Announcements and resource pages
- Search functionality
- SQLite database managed through SQLAlchemy and Flask-Migrate
- Unit and Selenium tests

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-WTF
- SQLite
- HTML
- CSS
- JavaScript
- Bootstrap Icons
- Pytest
- Selenium

## Group Members

| UWA ID | Name | GitHub Username |
|---|---|---|
| 24570238 | Qiumei Wang | merylwang86 |
| 24700839 | Varshitha Raparla | raparlavarshitha-glitch |
| 24661999 | Hans Lionar | hplionar |

## Project Structure

```text
CITS5505/
├── app/
│   ├── auth/
│   ├── main/
│   ├── models/
│   ├── static/
│   ├── templates/
│   └── __init__.py
├── migrations/
├── scripts/
├── tests/
├── config.py
├── requirements.txt
├── run.py
├── run_project.md
└── README.md
```


## Running the Application Locally

These instructions assume you are running the commands from the project root directory.

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Apply database migrations

```powershell
python -m flask --app app:create_app db upgrade
```

If multiple migration heads are present, run:

```powershell
python -m flask --app app:create_app db upgrade heads
```

### 4. Seed development data

```powershell
python scripts/seed_dev_db.py
```

### 5. Run the application

```powershell
python run.py
```

Then open the application in your browser:

```text
http://127.0.0.1:5000
```

To stop the server, press `Ctrl + C` in the terminal.

## Running Tests

Run the full test suite:

```powershell
python -m pytest -q
```

Run only the unit tests:

```powershell
python -m pytest tests/test_unit.py -q
```

Run only the Selenium tests:

```powershell
python -m pytest tests/test_selenium.py -q
```

The Selenium tests require Google Chrome and Selenium WebDriver support. These tests use a live Flask server fixture to test the application through the browser.