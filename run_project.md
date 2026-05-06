## 1. Install dependencies first
python -m pip install -r requirements.txt

## 2. run
python run.py

The app creates the SQLite tables automatically on startup.
If the database has no study sessions, it also creates demo Study Buddy data.

## 3. optional: reset development demo data
python scripts/seed_dev_db.py

This creates demo users:
- hlionar / passwd
- matthew.daggitt@uwa.edu.au / passwd
- admin / admin

## 4. browse the app
http://127.0.0.1:5000

## 5. exit
ctrl + c
