from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import or_

from app import db
from app.models import User, StudySession, SessionMessage

main = Blueprint("main", __name__)


# ---------- Login ----------
def get_current_user():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    return db.session.get(User, user_id)

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("main.login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# ---------- Auth ----------
@main.route("/")
def index():
    return redirect(url_for("main.login"))


@main.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            or_(
                User.username == identifier,
                User.email == identifier
            )
        ).first()

        if user is None:
            error = "Account not found. Please register first."
            return render_template("auth/login.html", error=error)

        if not user.check_password(password):
            error = "Incorrect password."
            return render_template("auth/login.html", error=error)

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username

        return redirect(url_for("main.studybuddy"))

    return render_template("auth/login.html", error=error)

@main.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/api/check-username")
def check_username():
    username = request.args.get("username", "").strip()

    if not username:
        return jsonify({
            "available": False,
            "message": ""
        })

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({
            "available": False,
            "message": "Username unavailable. Try something else."
        })

    return jsonify({
        "available": True,
        "message": "Looks good — this username is available."
    })

@main.route("/api/check-email")
def check_email():
    email = request.args.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "available": False,
            "message": ""
        })

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "available": False,
            "message": "Email is already registered."
        })

    return jsonify({
        "available": True,
        "message": ""
    })

@main.route("/register", methods=["GET", "POST"])
def register():
    form_data = {
        "username": "",
        "email": "",
    }

    field_errors = {}
    field_success = {}

    if request.method == "POST":
        form_data["username"] = request.form.get("username", "").strip()
        form_data["email"] = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Username validation
        if not form_data["username"]:
            field_errors["username"] = "Username is required."
        elif User.query.filter_by(username=form_data["username"]).first():
            field_errors["username"] = "Username unavailable. Try something else."
        else:
            field_success["username"] = "Looks good — this username is available."

        # Email validation
        if not form_data["email"]:
            field_errors["email"] = "Email is required."
        elif User.query.filter_by(email=form_data["email"]).first():
            field_errors["email"] = "Email is already registered."

        # Password validation
        if not password:
            field_errors["password"] = "Password is required."
        elif len(password) < 8:
            field_errors["password"] = "Password must be at least 8 characters."
        elif not any(char.isalpha() for char in password):
            field_errors["password"] = "Use at least one letter and one number."
        elif not any(char.isdigit() for char in password):
            field_errors["password"] = "Use at least one letter and one number."
        else:
            field_success["password"] = "Password looks good."

        # Confirm password validation
        if not confirm_password:
            field_errors["confirm_password"] = "Please confirm your password."
        elif password and password != confirm_password:
            field_errors["confirm_password"] = "Passwords do not match."
        elif password and "password" not in field_errors:
            field_success["confirm_password"] = "Passwords match."

        # If there are validation errors, stay on register page
        if field_errors:
            return render_template(
                "auth/register.html",
                form_data=form_data,
                field_errors=field_errors,
                field_success=field_success,
            )

        # Create account only after all validation passes
        user = User(
            username=form_data["username"],
            email=form_data["email"],
            role=User.ROLE_STUDENT,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("main.login"))

    return render_template(
        "auth/register.html",
        form_data=form_data,
        field_errors=field_errors,
        field_success=field_success,
    )

@main.route("/test-base")
def test_base():
    return render_template("test_base.html")

# ---------- Home ----------
@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html")

# ---------- StudyBuddy ----------
@main.route("/studybuddy")
@login_required
def studybuddy():
    sessions = StudySession.query.order_by(StudySession.id.desc()).all()
    current_user = get_current_user()

    joined_ids = {s.id for s in current_user.joined}
    saved_ids = {s.id for s in current_user.saved}
    hosted_ids = {s.id for s in current_user.hosted_sessions}

    return render_template(
        "studybuddy.html",
        sessions=sessions,
        joined_ids=joined_ids,
        saved_ids=saved_ids,
        hosted_ids=hosted_ids
    )


@main.route("/studybuddy/create", methods=["POST"])
@login_required
def create_session():
    current_user = get_current_user()

    unit_code = request.form.get("unit_code", "").strip()
    topic = request.form.get("topic", "").strip()
    description = request.form.get("description", "").strip()
    host_name = request.form.get("host_name", "").strip()
    day = request.form.get("day", "").strip()
    time = request.form.get("time", "").strip()
    mode = request.form.get("mode", "").strip()
    capacity_raw = request.form.get("capacity", "").strip()

    if not all([unit_code, topic, description, host_name, day, time, mode, capacity_raw]):
        return redirect(url_for("main.studybuddy"))

    try:
        capacity = int(capacity_raw)
    except ValueError:
        return redirect(url_for("main.studybuddy"))

    if capacity < 2:
        return redirect(url_for("main.studybuddy"))

    new_session = StudySession(
        unit_code=unit_code.upper(),
        topic=topic,
        description=description,
        host_name=host_name,
        day=day,
        time=time,
        mode=mode,
        capacity=capacity,
        joined_count=1,
        host_id=current_user.id
    )

    db.session.add(new_session)
    db.session.commit()

    if new_session not in current_user.joined:
        current_user.joined.append(new_session)
        db.session.commit()

    return redirect(url_for("main.studybuddy"))


# ---------- Join / Leave ----------
@main.route("/sessions/<int:session_id>/join", methods=["POST"])
@login_required
def join_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session not in current_user.joined and session.joined_count < session.capacity:
        current_user.joined.append(session)
        session.joined_count += 1
        db.session.commit()

    return redirect(url_for("main.session_detail", session_id=session.id))


@main.route("/sessions/<int:session_id>/leave", methods=["POST"])
@login_required
def leave_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session in current_user.joined:
        current_user.joined.remove(session)
        session.joined_count = max(0, session.joined_count - 1)
        db.session.commit()

    return redirect(url_for("main.my_sessions", view="joined"))


# ---------- Save ----------
@main.route("/sessions/<int:session_id>/save", methods=["POST"])
@login_required
def save_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session not in current_user.saved:
        current_user.saved.append(session)
        db.session.commit()

    return redirect(url_for("main.studybuddy"))


@main.route("/sessions/<int:session_id>/unsave", methods=["POST"])
@login_required
def unsave_session(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    if session in current_user.saved:
        current_user.saved.remove(session)
        db.session.commit()

    return redirect(url_for("main.my_sessions", view="saved"))


# ---------- My Sessions ----------
@main.route("/my-sessions")
@login_required
def my_sessions():
    current_user = get_current_user()
    view = request.args.get("view", "all")

    if view == "joined":
        sessions = current_user.joined
    elif view == "saved":
        sessions = current_user.saved
    elif view == "hosted":
        sessions = current_user.hosted_sessions
    else:
        ids = {s.id for s in current_user.joined + current_user.saved + current_user.hosted_sessions}
        sessions = StudySession.query.filter(StudySession.id.in_(ids)).all() if ids else []

    return render_template(
        "my_sessions.html",
        sessions=sessions,
        current_view=view
    )


# ---------- Session Detail ----------
@main.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
    current_user = get_current_user()
    session = StudySession.query.get_or_404(session_id)

    messages = SessionMessage.query.filter_by(
        session_id=session.id,
        parent_id=None
    ).order_by(SessionMessage.created_at.desc()).all()

    joined_ids = {u.id for u in session.joined_users}
    is_joined = current_user.id in joined_ids

    return render_template(
        "session_detail.html",
        session=session,
        messages=messages,
        current_user=current_user,
        is_joined=is_joined
    )


# ---------- Messages ----------
@main.route("/sessions/<int:session_id>/messages", methods=["POST"])
@login_required
def add_message(session_id):
    current_user = get_current_user()
    content = request.form.get("content", "").strip()

    if content:
        message = SessionMessage(
            session_id=session_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(message)
        db.session.commit()

    return redirect(url_for("main.session_detail", session_id=session_id))


@main.route("/sessions/<int:session_id>/messages/<int:message_id>/reply", methods=["POST"])
@login_required
def reply_message(session_id, message_id):
    current_user = get_current_user()
    content = request.form.get("content", "").strip()

    if content:
        reply = SessionMessage(
            session_id=session_id,
            user_id=current_user.id,
            parent_id=message_id,
            content=content
        )
        db.session.add(reply)
        db.session.commit()

    return redirect(url_for("main.session_detail", session_id=session_id))