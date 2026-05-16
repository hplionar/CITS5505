# Running CSHub Locally

These instructions assume Windows PowerShell from the project root.

## 1. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## 2. Configure Environment Variables

The app reads configuration from environment variables. For local development, set at least a secret key:

```powershell
$env:SECRET_KEY="replace-this-with-a-local-secret"
```

The default database is `instance/studyhub.db`. To use a different SQLite database:

```powershell
$env:DATABASE_URL="sqlite:///instance/studyhub.db"
```

Optional legacy flags exist for quick local setup, but team development should use migrations instead:

```powershell
$env:AUTO_CREATE_DATABASE="0"
$env:AUTO_SEED_DEMO_DATA="0"
```

## 3. Apply Database Migrations

Create or update the local database schema with Flask-Migrate:

```powershell
flask --app app:create_app db upgrade
```

When a model changes, generate a migration, review the generated file, then upgrade:

```powershell
flask --app app:create_app db migrate -m "Describe schema change"
flask --app app:create_app db upgrade
```

Migration files are stored in `migrations/versions/` and should be committed with the model changes.

## 4. Seed Development Data

```powershell
python scripts/seed_dev_db.py
```

Demo users include:

- `hlionar` / `passwd`
- `matthew.daggitt@uwa.edu.au` / `passwd`
- `admin` / `admin`

## 5. Run The App

```powershell
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

Stop the server with `Ctrl+C`.

## 6. Run Tests

Run the unit and Selenium test suite:

```powershell
python -m pytest
```

The Selenium tests use a live Flask server from the test fixtures and require:

- Google Chrome installed
- A compatible ChromeDriver available to Selenium
- The `selenium` package installed from `requirements.txt`

If ChromeDriver is unavailable, the Selenium tests are skipped. Once ChromeDriver is installed correctly, `python -m pytest tests/test_selenium.py` should run the browser tests against the live test server.
