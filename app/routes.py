from datetime import datetime
from functools import wraps
from datetime import date
import re

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import or_

from app import db
from app.models import (
    Announcement,
    User,
    StudySession,
    SessionMessage,
    SessionReadState,
    ForumThread,
    ForumReply,
    ForumTag,
)

main = Blueprint("main", __name__)

# ---------- Forum Time ----------
@main.app_template_filter("forum_time")
def forum_time(value):
    """Display recent forum activity as relative time, otherwise as a date."""
    if value is None:
        return ""

    now = datetime.utcnow()
    elapsed = now - value
    seconds = int(elapsed.total_seconds())

    if seconds < 60:
        return "Just now"

    minutes = seconds // 60
    if minutes < 60:
        if minutes == 1:
            return "1 min ago"
        return f"{minutes} mins ago"

    hours = minutes // 60
    if hours < 24:
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"

    return value.strftime("%d %b %Y")


# ---------- Login ----------
def get_current_user():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    return db.session.get(User, user_id)


@main.app_context_processor
def inject_topbar_notifications():
    current_user = get_current_user()

    if current_user is None:
        return {
            "current_user": None,
            "session_notifications": [],
            "session_notification_count": 0,
        }

    joined_session_ids = [study_session.id for study_session in current_user.joined]

    if not joined_session_ids:
        return {
            "current_user": current_user,
            "session_notifications": [],
            "session_notification_count": 0,
        }

    read_states = {
        read_state.session_id: read_state.last_read_message_id
        for read_state in SessionReadState.query.filter(
            SessionReadState.user_id == current_user.id,
            SessionReadState.session_id.in_(joined_session_ids),
        ).all()
    }

    candidate_messages = (
        SessionMessage.query.filter(
            SessionMessage.session_id.in_(joined_session_ids),
            SessionMessage.user_id != current_user.id,
        )
        .order_by(SessionMessage.created_at.desc(), SessionMessage.id.desc())
        .all()
    )

    unread_messages = [
        message
        for message in candidate_messages
        if message.id > read_states.get(message.session_id, 0)
    ]

    return {
        "current_user": current_user,
        "session_notifications": unread_messages[:8],
        "session_notification_count": len(unread_messages),
    }


def mark_session_messages_read(current_user, session_id):
    latest_message = (
        SessionMessage.query.filter_by(session_id=session_id)
        .order_by(SessionMessage.id.desc())
        .first()
    )

    if latest_message is None:
        return

    read_state = SessionReadState.query.filter_by(
        user_id=current_user.id,
        session_id=session_id,
    ).first()

    if read_state is None:
        read_state = SessionReadState(
            user_id=current_user.id,
            session_id=session_id,
            last_read_message_id=latest_message.id,
        )
        db.session.add(read_state)
    else:
        read_state.last_read_message_id = max(
            read_state.last_read_message_id,
            latest_message.id,
        )

    db.session.commit()

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("main.login"))

        return view_function(*args, **kwargs)

    return wrapped_view


def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        current_user = get_current_user()

        if current_user is None:
            return redirect(url_for("main.login"))

        if not current_user.is_admin():
            return redirect(url_for("main.announcements"))

        return view_function(*args, **kwargs)

    return wrapped_view


def make_unique_slug(title):
    base_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base_slug = base_slug or "announcement"
    slug = base_slug
    counter = 2

    while Announcement.query.filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def get_day_label(session_date):
    return session_date.strftime("%a")


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

        return redirect(url_for("main.home"))

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
        "message": "Looks good - this username is available."
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
            field_success["username"] = "Looks good - this username is available."

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

# ---------- Forum ----------
@main.route("/forum")
@login_required
def forum():
    current_user = get_current_user()
    current_sort = request.args.get("sort", "recent")

    available_tags = (
        ForumTag.query
        .filter_by(is_active=True)
        .order_by(ForumTag.name.asc())
        .all()
    )

    if current_sort == "new":
        threads = (
            ForumThread.query
            .order_by(
                ForumThread.is_pinned.desc(),
                ForumThread.created_at.desc()
            )
            .all()
        )

    elif current_sort == "popular":
        threads = ForumThread.query.all()

        threads.sort(
            key=lambda thread: (
                thread.is_pinned,
                thread.like_count * 2 + thread.reply_count
            ),
            reverse=True
        )

    else:
        current_sort = "recent"

        threads = (
            ForumThread.query
            .order_by(
                ForumThread.is_pinned.desc(),
                ForumThread.updated_at.desc()
            )
            .all()
        )

    return render_template(
        "forum.html",
        threads=threads,
        current_sort=current_sort,
        current_user=current_user,
        available_tags=available_tags
    )


def normalize_forum_tags(raw_tags):
    tags = []
    seen = set()

    for tag in raw_tags.split(","):
        cleaned_tag = tag.strip().lstrip("#").lower()

        if cleaned_tag and cleaned_tag not in seen:
            tags.append(cleaned_tag[:40])
            seen.add(cleaned_tag)

        if len(tags) == 5:
            break

    return ",".join(tags)


@main.route("/forum/thread/<int:thread_id>")
@login_required
def thread_detail(thread_id):
    thread = ForumThread.query.get_or_404(thread_id)

    replies = (
        ForumReply.query
        .filter_by(thread_id=thread.id)
        .order_by(ForumReply.created_at.asc())
        .all()
    )

    return render_template(
        "thread_detail.html",
        thread=thread,
        replies=replies
    )


@main.route("/forum/thread/create", methods=["POST"])
@login_required
def create_thread():
    current_user = get_current_user()

    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    category = request.form.get("category", "General").strip() or "General"

    if not title or not body:
        return redirect(url_for("main.forum"))

    raw_tag_ids = request.form.getlist("tag_ids")
    selected_tag_ids = []

    for raw_id in raw_tag_ids:
        try:
            tag_id = int(raw_id)
        except ValueError:
            continue

        if tag_id not in selected_tag_ids:
            selected_tag_ids.append(tag_id)

    selected_tag_ids = selected_tag_ids[:3]

    selected_tags = []

    if selected_tag_ids:
        selected_tags = (
            ForumTag.query
            .filter(
                ForumTag.id.in_(selected_tag_ids),
                ForumTag.is_active.is_(True)
            )
            .all()
        )

    thread = ForumThread(
        title=title,
        body=body,
        category=category,
        author=current_user
    )

    thread.tags = selected_tags

    db.session.add(thread)
    db.session.commit()

    return redirect(url_for("main.thread_detail", thread_id=thread.id))


@main.route("/forum/thread/<int:thread_id>/reply", methods=["POST"])
@login_required
def reply_thread(thread_id):
    current_user = get_current_user()
    thread = ForumThread.query.get_or_404(thread_id)

    body = request.form.get("body", "").strip()

    if body:
        reply = ForumReply(
            body=body,
            thread=thread,
            author=current_user
        )

        # Update thread activity so "Recently Active" sorting reflects new replies.
        thread.updated_at = db.func.now()

        db.session.add(reply)
        db.session.commit()

    return redirect(url_for("main.thread_detail", thread_id=thread.id))


@main.route("/forum/thread/<int:thread_id>/like", methods=["POST"])
@login_required
def toggle_thread_like(thread_id):
    current_user = get_current_user()
    thread = ForumThread.query.get_or_404(thread_id)

    if current_user in thread.liked_by:
        thread.liked_by.remove(current_user)
        liked = False
    else:
        thread.liked_by.append(current_user)
        liked = True

    db.session.commit()

    return jsonify({
        "liked": liked,
        "likeCount": thread.like_count
    })


@main.route("/forum/thread/<int:thread_id>/save", methods=["POST"])
@login_required
def toggle_thread_save(thread_id):
    current_user = get_current_user()
    thread = ForumThread.query.get_or_404(thread_id)

    if current_user in thread.saved_by:
        thread.saved_by.remove(current_user)
        saved = False
    else:
        thread.saved_by.append(current_user)
        saved = True

    db.session.commit()

    return jsonify({
        "saved": saved
    })


# ---------- Home ----------
@main.route("/home")
@login_required
def home():
    current_user = get_current_user()

    joined_sessions = list(current_user.joined)
    saved_sessions = list(current_user.saved)

    recent_messages = (
        SessionMessage.query
        .order_by(SessionMessage.created_at.desc(), SessionMessage.id.desc())
        .limit(3)
        .all()
    )

    recent_activity = []

    for message in recent_messages:
        message_user = db.session.get(User, message.user_id)
        study_session = db.session.get(StudySession, message.session_id)

        recent_activity.append({
            "username": message_user.username if message_user else "Student",
            "initial": message_user.username[0].upper()
            if message_user and message_user.username
            else "S",
            "topic": study_session.topic if study_session else "Study discussion",
            "content": message.content,
            "session_id": message.session_id,
        })

    joined_sessions_data = []

    for study_session in joined_sessions:
        session_date_value = None
        session_date_label = None

        if hasattr(study_session, "session_date") and study_session.session_date:
            session_date_value = study_session.session_date.isoformat()
            session_date_label = study_session.session_date.strftime("%d %b %Y")

        joined_sessions_data.append({
            "id": study_session.id,
            "topic": study_session.topic,
            "day": study_session.day,
            "date": session_date_value,
            "session_date": session_date_value,
            "time": study_session.time,
            "mode": study_session.mode,
            "location": study_session.location,
            "unit_code": study_session.unit_code,
            "reminder_date": session_date_value,
            "reminder_label": session_date_label,
        })

    recommended_sessions = (
        StudySession.query
        .order_by(StudySession.id.desc())
        .limit(2)
        .all()
    )

    today = date.today()

    return render_template(
        "home.html",
        current_user=current_user,
        joined_sessions=joined_sessions,
        saved_sessions=saved_sessions,
        recent_activity=recent_activity,
        recommended_sessions=recommended_sessions,
        joined_sessions_data=joined_sessions_data,
        forum_discussion_count=len(recent_activity),
        study_buddy_count=len(joined_sessions),
        saved_topics_count=len(saved_sessions),
        current_month=today.month,
        current_year=today.year,
    )

@main.route("/help")
@login_required
def help_page():
    return render_template("help.html")


@main.route("/rules")
@login_required
def rules():
    return render_template("rules.html")


@main.route("/announcements")
@login_required
def announcements():
    current_user = get_current_user()
    announcement_items = Announcement.query.order_by(
        Announcement.created_at.desc(),
        Announcement.id.desc()
    ).all()

    return render_template(
        "announcements.html",
        announcements=announcement_items,
        current_user=current_user,
    )


@main.route("/announcements/create", methods=["POST"])
@admin_required
def create_announcement():
    current_user = get_current_user()

    category = request.form.get("category", "").strip()
    date_label = request.form.get("date_label", "").strip()
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    details = request.form.get("details", "").strip()

    if not all([category, date_label, title, body, details]):
        return redirect(url_for("main.announcements"))

    announcement = Announcement(
        slug=make_unique_slug(title),
        category=category,
        date_label=date_label,
        title=title,
        body=body,
        details=details,
        author_id=current_user.id,
    )

    db.session.add(announcement)
    db.session.commit()

    return redirect(url_for("main.announcements"))


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
    session_date_raw = request.form.get("session_date", "").strip()
    time = request.form.get("time", "").strip()
    mode = request.form.get("mode", "").strip()
    location = request.form.get("location", "").strip()
    capacity_raw = request.form.get("capacity", "").strip()

    if not all([unit_code, topic, description, host_name, session_date_raw, time, mode, capacity_raw]):
        return redirect(url_for("main.studybuddy"))

    if mode in {"in-person", "hybrid"} and not location:
        return redirect(url_for("main.studybuddy"))

    try:
        capacity = int(capacity_raw)
    except ValueError:
        return redirect(url_for("main.studybuddy"))

    try:
        session_date = date.fromisoformat(session_date_raw)
    except ValueError:
        return redirect(url_for("main.studybuddy"))

    if capacity < 2:
        return redirect(url_for("main.studybuddy"))

    new_session = StudySession(
        unit_code=unit_code.upper(),
        topic=topic,
        description=description,
        host_name=host_name,
        session_date=session_date,
        day=get_day_label(session_date),
        time=time,
        mode=mode,
        location=location or None,
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

    if is_joined:
        mark_session_messages_read(current_user, session.id)

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


# ---------- Messages ----------
@main.route("/profile")
@login_required
def profile():
    current_user = get_current_user()

    return render_template(
        "profile.html",
        current_user=current_user
    )