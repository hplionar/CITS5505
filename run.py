from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    if db.session.get(User, 1) is None:
        user = User(id=1, username="Demo User")
        db.session.add(user)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)