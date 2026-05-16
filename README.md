# CSHub

CSHub is a Flask-based web application for UWA Computer Science and Software Engineering students to communicate, share information, and organise study activities in one place. The application combines a community forum, announcements, Study Buddy sessions, user profiles, notifications, search, and saved content.

## Design and Use

CSHub is designed to be:

- **Engaging:** a clean dark interface with clear cards, icons, and focused navigation.
- **Effective:** practical support for discussion, peer help, search, study-session organisation, announcements, notifications, and saved resources.
- **Intuitive:** common actions such as creating posts, replying, searching, joining sessions, saving content, and viewing profiles are available through consistent UI patterns.

Users can register and log in, create forum posts, comment on discussions, like and save forum threads, search for content, join or save Study Buddy sessions, receive session message notifications, and view profile activity. User data is stored in SQLite and managed through SQLAlchemy and Flask-Migrate.

## Features

- User registration, login, and logout
- Password hashing
- CSRF protection
- Forum threads and nested replies
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
|-- app/
|   |-- models/
|   |-- static/
|   |-- templates/
|   `-- __init__.py
|-- migrations/
|-- scripts/
|-- tests/
|-- config.py
|-- requirements.txt
|-- run.py
|-- run_project.md
`-- README.md
```

## Running the Application Locally

Run these commands from the project root directory.

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

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

The committed migration history has a single head. If this command reports multiple heads, pull the latest repository changes before running it again.

### 4. Seed development data

```powershell
python scripts/seed_dev_db.py
```

Demo users include:

- `hlionar` / `passwd`
- `vraparla` / `passwd`
- `qwang` / `passwd`
- `matthew.daggitt@uwa.edu.au` / `passwd`
- `admin` / `admin`

### 5. Run the application

```powershell
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

Stop the server with `Ctrl+C`.

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

The Selenium tests require Google Chrome and Selenium WebDriver support. If ChromeDriver is unavailable, the Selenium tests are skipped.
