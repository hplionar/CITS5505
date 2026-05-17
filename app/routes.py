from datetime import date, datetime, timedelta
from functools import wraps
import re
from collections import defaultdict

from flask import abort, Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from app import db
from app.models.associations import joined_sessions
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

from app.models.forum import FORUM_CATEGORIES, FORUM_CATEGORY_DESCRIPTIONS


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

    if not current_user.notify_study_messages:
        return {
            "current_user": current_user,
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


def build_search_like(query):
    return f"%{query}%"


def sort_search_items(items):
    return sorted(
        items,
        key=lambda item: item.get("created_at") or datetime.min,
        reverse=True,
    )


def is_valid_password(password):
    return (
        len(password) >= 8
        and any(char.isalpha() for char in password)
        and any(char.isdigit() for char in password)
    )


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
                User.email == identifier,
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
            "message": "",
        })

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({
            "available": False,
            "message": "Username unavailable. Try something else.",
        })

    return jsonify({
        "available": True,
        "message": "Looks good - this username is available.",
    })


@main.route("/api/check-email")
def check_email():
    email = request.args.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "available": False,
            "message": "",
        })

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "available": False,
            "message": "Email is already registered.",
        })

    return jsonify({
        "available": True,
        "message": "",
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

        if not form_data["username"]:
            field_errors["username"] = "Username is required."
        elif User.query.filter_by(username=form_data["username"]).first():
            field_errors["username"] = "Username unavailable. Try something else."
        else:
            field_success["username"] = "Looks good - this username is available."

        if not form_data["email"]:
            field_errors["email"] = "Email is required."
        elif User.query.filter_by(email=form_data["email"]).first():
            field_errors["email"] = "Email is already registered."

        if not password:
            field_errors["password"] = "Password is required."
        elif not is_valid_password(password):
            field_errors["password"] = "Use at least one letter and one number."
        else:
            field_success["password"] = "Password looks good."

        if not confirm_password:
            field_errors["confirm_password"] = "Please confirm your password."
        elif password and password != confirm_password:
            field_errors["confirm_password"] = "Passwords do not match."
        elif password and "password" not in field_errors:
            field_success["confirm_password"] = "Passwords match."

        if field_errors:
            return render_template(
                "auth/register.html",
                form_data=form_data,
                field_errors=field_errors,
                field_success=field_success,
            )

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
FORUM_PAGE_SIZE = 20


def get_forum_filters():
    current_sort = request.args.get("sort", "recent").strip().lower()
    current_category = request.args.get("category", "").strip()

    sort_aliases = {
        "best": "popular",
        "newest": "new",
        "oldest": "old",
    }

    current_sort = sort_aliases.get(current_sort, current_sort)

    if current_sort not in {"recent", "popular", "new", "old"}:
        current_sort = "recent"

    if current_category not in FORUM_CATEGORIES:
        current_category = ""

    return current_sort, current_category


def get_filtered_forum_threads(current_sort, current_category):
    thread_query = ForumThread.query

    if current_category:
        thread_query = thread_query.filter(ForumThread.category == current_category)

    if current_sort == "new":
        return (
            thread_query
            .order_by(
                ForumThread.is_pinned.desc(),
                ForumThread.created_at.desc(),
            )
            .all()
        )

    if current_sort == "old":
        return (
            thread_query
            .order_by(
                ForumThread.is_pinned.desc(),
                ForumThread.created_at.asc(),
            )
            .all()
        )

    if current_sort == "popular":
        threads = thread_query.all()
        threads.sort(
            key=lambda thread: (
                thread.is_pinned,
                thread.like_count * 2 + thread.reply_count,
                thread.updated_at or thread.created_at,
            ),
            reverse=True,
        )
        return threads

    return (
        thread_query
        .order_by(
            ForumThread.is_pinned.desc(),
            ForumThread.updated_at.desc(),
        )
        .all()
    )


def paginate_threads(threads, page, per_page=FORUM_PAGE_SIZE):
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    return threads[start_index:end_index], end_index < len(threads)


@main.route("/forum")
@login_required
def forum():
    current_user = get_current_user()
    current_sort, current_category = get_forum_filters()

    available_tags = (
        ForumTag.query
        .filter_by(is_active=True)
        .order_by(ForumTag.name.asc())
        .all()
    )

    all_threads = get_filtered_forum_threads(current_sort, current_category)
    threads, has_more_threads = paginate_threads(all_threads, page=1)

    if current_category:
        category_title = current_category
        category_description = FORUM_CATEGORY_DESCRIPTIONS[current_category]
    else:
        category_title = "All Threads"
        category_description = ""

    return render_template(
        "forum.html",
        threads=threads,
        has_more_threads=has_more_threads,
        next_page=2,
        current_sort=current_sort,
        current_category=current_category,
        category_title=category_title,
        category_description=category_description,
        forum_categories=FORUM_CATEGORIES,
        forum_category_descriptions=FORUM_CATEGORY_DESCRIPTIONS,
        current_user=current_user,
        available_tags=available_tags,
    )


@main.route("/forum/api/threads")
@login_required
def forum_threads_api():
    current_user = get_current_user()
    current_sort, current_category = get_forum_filters()

    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    all_threads = get_filtered_forum_threads(current_sort, current_category)
    threads, has_more_threads = paginate_threads(all_threads, page=page)

    html = render_template(
        "_forum_thread_cards.html",
        threads=threads,
        current_user=current_user,
    )

    return jsonify({
        "html": html,
        "has_more": has_more_threads,
        "next_page": page + 1,
    })


def normalize_forum_tags(raw_tags):
    tags = []
    seen = set()

    if not raw_tags:
        return tags

    for raw_tag in raw_tags.split(","):
        cleaned = raw_tag.strip().lower()

        if not cleaned:
            continue

        cleaned = cleaned.replace("#", "")
        slug = cleaned.replace(" ", "-")

        if slug and slug not in seen:
            tags.append(slug)
            seen.add(slug)

    return tags


def build_reply_tree(replies):
    reply_nodes = {}

    for reply in replies:
        reply_nodes[reply.id] = {
            "reply": reply,
            "children": [],
            "reply_count": 0,
        }

    roots = []

    for reply in replies:
        node = reply_nodes[reply.id]

        if reply.parent_id and reply.parent_id in reply_nodes:
            reply_nodes[reply.parent_id]["children"].append(node)
        else:
            roots.append(node)

    def count_replies(node):
        total = 0

        for child in node["children"]:
            total += 1
            total += count_replies(child)

        node["reply_count"] = total
        return total

    for root in roots:
        count_replies(root)

    return roots

    for reply in replies:
        reply_nodes[reply.id] = {
            "reply": reply,
            "children": [],
            "reply_count": 0
        }

    roots = []

    for reply in replies:
        node = reply_nodes[reply.id]

        if reply.parent_id and reply.parent_id in reply_nodes:
            reply_nodes[reply.parent_id]["children"].append(node)
        else:
            roots.append(node)

    def count_nested_replies(nodes):
        for node in nodes:
            count_nested_replies(node["children"])
            node["reply_count"] = len(node["children"])

            for child in node["children"]:
                node["reply_count"] += child["reply_count"]

    count_nested_replies(roots)

    return roots


def build_reply_tree(replies):
    reply_nodes = {}

    for reply in replies:
        reply_nodes[reply.id] = {
            "reply": reply,
            "children": [],
            "reply_count": 0,
        }

    roots = []

    for reply in replies:
        node = reply_nodes[reply.id]

        if reply.parent_id and reply.parent_id in reply_nodes:
            reply_nodes[reply.parent_id]["children"].append(node)
        else:
            roots.append(node)

    def count_nested_replies(nodes):
        for node in nodes:
            count_nested_replies(node["children"])
            node["reply_count"] = len(node["children"])

            for child in node["children"]:
                node["reply_count"] += child["reply_count"]

    count_nested_replies(roots)

    return roots


@main.route("/forum/thread/<int:thread_id>")
@login_required
def thread_detail(thread_id):
    current_user = get_current_user()
    thread = ForumThread.query.get_or_404(thread_id)

    replies = (
        ForumReply.query
        .filter_by(thread_id=thread.id)
        .order_by(ForumReply.created_at.asc(), ForumReply.id.asc())
        .all()
    )

    reply_tree = build_reply_tree(replies)

    return render_template(
        "thread_detail.html",
        thread=thread,
        replies=replies,
        reply_tree=reply_tree,
        reply_total=len(replies),
        current_user=current_user,
    )


@main.route("/forum/thread/create", methods=["POST"])
@login_required
def create_thread():
    current_user = get_current_user()

    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    category = request.form.get("category", "General").strip() or "General"

    if category not in FORUM_CATEGORIES:
        category = "General"

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
                ForumTag.is_active.is_(True),
            )
            .all()
        )

    thread = ForumThread(
        title=title,
        body=body,
        category=category,
        author=current_user,
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
    parent_id_raw = request.form.get("parent_id", "").strip()

    parent_reply = None

    if parent_id_raw:
        try:
            parent_id = int(parent_id_raw)
        except ValueError:
            parent_id = None

        if parent_id is not None:
            parent_reply = (
                ForumReply.query
                .filter_by(id=parent_id, thread_id=thread.id)
                .first()
            )

        if parent_reply is None:
            return redirect(url_for("main.thread_detail", thread_id=thread.id) + "#comments")

    if body:
        reply = ForumReply(
            body=body,
            thread=thread,
            author=current_user,
            parent=parent_reply,
        )

        thread.updated_at = db.func.now()

        db.session.add(reply)
        db.session.commit()

    return redirect(url_for("main.thread_detail", thread_id=thread.id) + "#comments")


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
        "likeCount": thread.like_count,
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
        "saved": saved,
    })


@main.route("/forum/reply/<int:reply_id>/delete", methods=["POST"])
@login_required
def delete_forum_reply(reply_id):
    current_user = get_current_user()
    reply = ForumReply.query.get_or_404(reply_id)
    thread_id = reply.thread_id

    if reply.author_id != current_user.id:
        return redirect(url_for("main.thread_detail", thread_id=thread_id) + "#comments")

    has_children = ForumReply.query.filter_by(parent_id=reply.id).first() is not None

    if has_children:
        reply.body = ""
        reply.is_deleted = True
    else:
        db.session.delete(reply)

    reply.thread.updated_at = db.func.now()
    db.session.commit()

    return redirect(url_for("main.thread_detail", thread_id=thread_id) + "#comments")

# ---------- Home ----------
@main.route("/home")
@login_required
def home():
    current_user = get_current_user()

    joined_sessions = list(current_user.joined)
    saved_sessions = list(current_user.saved)

    activity_feed = []

    # 1. Recent Study Buddy messages
    recent_messages = (
        SessionMessage.query
        .order_by(SessionMessage.created_at.desc(), SessionMessage.id.desc())
        .limit(5)
        .all()
    )

    for message in recent_messages:
        message_user = db.session.get(User, message.user_id)
        study_session = db.session.get(StudySession, message.session_id)

        activity_feed.append({
            "type": "message",
            "icon": "💬",
            "title": f"{message_user.username if message_user else 'Student'} posted in {study_session.topic if study_session else 'a study session'}",
            "description": message.content[:90],
            "link": url_for("main.session_detail", session_id=message.session_id),
        })

    # 2. Joined Study Buddy sessions
    for study_session in joined_sessions[:3]:
        activity_feed.append({
            "type": "joined",
            "icon": "👥",
            "title": f"You joined {study_session.topic}",
            "description": f"{study_session.day} · {study_session.time} · {study_session.mode.replace('-', ' ').title()}",
            "link": url_for("main.session_detail", session_id=study_session.id),
        })

    # 3. Saved Study Buddy sessions
    for study_session in saved_sessions[:3]:
        activity_feed.append({
            "type": "saved",
            "icon": "📌",
            "title": f"You saved {study_session.topic}",
            "description": f"{study_session.day} · {study_session.time} · {study_session.mode.replace('-', ' ').title()}",
            "link": url_for("main.session_detail", session_id=study_session.id),
        })

    # Keep the feed small for the Home dashboard
    activity_feed = activity_feed[:8]

    # This is the count shown on the Home page
    activity_count = len(activity_feed)
    
    # Count for Forum Snapshot card
    forum_discussion_count = ForumThread.query.count()

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
        activity_feed=activity_feed,
        activity_count=activity_count,
        recommended_sessions=recommended_sessions,
        joined_sessions_data=joined_sessions_data,
        forum_discussion_count=forum_discussion_count,
        study_buddy_count=len(joined_sessions),
        saved_topics_count=len(saved_sessions),
        current_month=today.month,
        current_year=today.year,
    )


@main.route("/search")
@login_required
def search_results():
    query = request.args.get("q", "").strip()
    active_tab = request.args.get("tab", "overview")

    if active_tab not in {"overview", "forum", "comments", "studybuddy"}:
        active_tab = "overview"

    forum_results = []
    comment_results = []
    studybuddy_results = []

    if query:
        like_query = build_search_like(query)

        forum_threads = (
            ForumThread.query
            .filter(
                or_(
                    ForumThread.title.ilike(like_query),
                    ForumThread.body.ilike(like_query),
                    ForumThread.category.ilike(like_query),
                )
            )
            .order_by(ForumThread.updated_at.desc())
            .limit(20)
            .all()
        )

        forum_results = [
            {
                "type": "Forum",
                "icon": "Q",
                "title": thread.title,
                "summary": thread.body,
                "url": url_for("main.thread_detail", thread_id=thread.id),
                "meta": thread.category,
                "created_at": thread.updated_at,
                "stats": [
                    f"{thread.like_count} likes",
                    f"{thread.reply_count} comments",
                ],
            }
            for thread in forum_threads
        ]

        forum_replies = (
            ForumReply.query
            .filter(ForumReply.body.ilike(like_query))
            .order_by(ForumReply.created_at.desc())
            .limit(20)
            .all()
        )

        session_messages = (
            SessionMessage.query
            .filter(SessionMessage.content.ilike(like_query))
            .order_by(SessionMessage.created_at.desc())
            .limit(20)
            .all()
        )

        comment_results = sort_search_items([
            {
                "type": "Forum comment",
                "icon": "C",
                "title": reply.thread.title if reply.thread else "Forum discussion",
                "summary": reply.body,
                "url": (
                    url_for("main.thread_detail", thread_id=reply.thread_id) + "#comments"
                ),
                "meta": reply.author.username if reply.author else "Student",
                "created_at": reply.created_at,
                "stats": ["Forum"],
            }
            for reply in forum_replies
        ] + [
            {
                "type": "Study Buddy comment",
                "icon": "C",
                "title": message.session.topic if message.session else "Study Buddy session",
                "summary": message.content,
                "url": url_for("main.session_detail", session_id=message.session_id),
                "meta": message.user.username if message.user else "Student",
                "created_at": message.created_at,
                "stats": ["Study Buddy"],
            }
            for message in session_messages
        ])

        study_sessions = (
            StudySession.query
            .filter(
                or_(
                    StudySession.unit_code.ilike(like_query),
                    StudySession.topic.ilike(like_query),
                    StudySession.description.ilike(like_query),
                    StudySession.host_name.ilike(like_query),
                    StudySession.mode.ilike(like_query),
                    StudySession.location.ilike(like_query),
                )
            )
            .order_by(StudySession.id.desc())
            .limit(20)
            .all()
        )

        studybuddy_results = [
            {
                "type": "Study Buddy",
                "icon": "S",
                "title": study_session.topic,
                "summary": study_session.description,
                "url": url_for("main.session_detail", session_id=study_session.id),
                "meta": study_session.unit_code,
                "created_at": None,
                "stats": [
                    f"{study_session.joined_count}/{study_session.capacity} joined",
                    study_session.mode.replace("-", " ").title(),
                ],
            }
            for study_session in study_sessions
        ]

    overview_results = sort_search_items(
        forum_results[:5]
        + comment_results[:5]
        + studybuddy_results[:5]
    )

    tab_results = {
        "overview": overview_results,
        "forum": forum_results,
        "comments": comment_results,
        "studybuddy": studybuddy_results,
    }

    return render_template(
        "search_results.html",
        search_query=query,
        active_tab=active_tab,
        results=tab_results[active_tab],
        result_counts={
            "overview": len(overview_results),
            "forum": len(forum_results),
            "comments": len(comment_results),
            "studybuddy": len(studybuddy_results),
        },
    )


@main.route("/help")
@login_required
def help_page():
    return render_template("help.html")


@main.route("/rules")
@login_required
def rules():
    return render_template("rules.html")


@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    current_user = get_current_user()

    if request.method == "POST":
        section = request.form.get("section", "")

        if section == "account":
            first_name = request.form.get("first_name", "").strip() or None
            last_name = request.form.get("last_name", "").strip() or None
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            bio = request.form.get("bio", "").strip() or None

            if not username or not email:
                flash("Username and email are required.", "error")
            elif User.query.filter(User.username == username, User.id != current_user.id).first():
                flash("That username is already taken.", "error")
            elif User.query.filter(User.email == email, User.id != current_user.id).first():
                flash("That email is already registered.", "error")
            else:
                current_user.first_name = first_name
                current_user.last_name = last_name
                current_user.username = username
                current_user.email = email
                current_user.bio = bio
                session["username"] = username
                db.session.commit()
                flash("Account settings updated.", "success")

        elif section == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_user.check_password(current_password):
                flash("Current password is incorrect.", "error")
            elif not is_valid_password(new_password):
                flash("New password must be at least 8 characters and include letters and numbers.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash("Password updated.", "success")

        elif section == "notifications":
            current_user.notify_study_messages = "notify_study_messages" in request.form
            current_user.notify_session_reminders = "notify_session_reminders" in request.form
            current_user.notify_announcements = "notify_announcements" in request.form
            db.session.commit()
            flash("Notification settings updated.", "success")

        elif section == "study":
            preferred_mode = request.form.get("preferred_study_mode", "").strip()
            current_user.preferred_study_mode = preferred_mode or None
            current_user.preferred_location = request.form.get("preferred_location", "").strip() or None
            current_user.interested_units = request.form.get("interested_units", "").strip() or None
            db.session.commit()
            flash("Study preferences updated.", "success")

        elif section == "privacy":
            current_user.show_full_name = "show_full_name" in request.form
            current_user.show_joined_sessions = "show_joined_sessions" in request.form
            current_user.show_saved_sessions = "show_saved_sessions" in request.form
            current_user.allow_profile_discovery = "allow_profile_discovery" in request.form
            db.session.commit()
            flash("Privacy settings updated.", "success")

        else:
            flash("Unknown settings section.", "error")

        return redirect(url_for("main.settings"))

    return render_template("settings.html", current_user=current_user)


@main.route("/announcements")
@login_required
def announcements():
    current_user = get_current_user()
    announcement_items = Announcement.query.order_by(
        Announcement.created_at.desc(),
        Announcement.id.desc(),
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

    joined_ids = {study_session.id for study_session in current_user.joined}
    saved_ids = {study_session.id for study_session in current_user.saved}
    hosted_ids = {study_session.id for study_session in current_user.hosted_sessions}

    return render_template(
        "studybuddy.html",
        sessions=sessions,
        joined_ids=joined_ids,
        saved_ids=saved_ids,
        hosted_ids=hosted_ids,
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
        host_id=current_user.id,
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
    study_session = StudySession.query.get_or_404(session_id)

    if study_session not in current_user.joined and study_session.joined_count < study_session.capacity:
        current_user.joined.append(study_session)
        study_session.joined_count += 1
        db.session.commit()

    return redirect(url_for("main.session_detail", session_id=study_session.id))


@main.route("/sessions/<int:session_id>/leave", methods=["POST"])
@login_required
def leave_session(session_id):
    current_user = get_current_user()
    study_session = StudySession.query.get_or_404(session_id)

    if study_session in current_user.joined:
        current_user.joined.remove(study_session)
        study_session.joined_count = max(0, study_session.joined_count - 1)
        db.session.commit()

    return redirect(url_for("main.my_sessions", view="joined"))


# ---------- Save ----------
@main.route("/sessions/<int:session_id>/save", methods=["POST"])
@login_required
def save_session(session_id):
    current_user = get_current_user()
    study_session = StudySession.query.get_or_404(session_id)

    if study_session not in current_user.saved:
        current_user.saved.append(study_session)
        db.session.commit()

    return redirect(url_for("main.studybuddy"))


@main.route("/sessions/<int:session_id>/unsave", methods=["POST"])
@login_required
def unsave_session(session_id):
    current_user = get_current_user()
    study_session = StudySession.query.get_or_404(session_id)

    if study_session in current_user.saved:
        current_user.saved.remove(study_session)
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
        ids = {
            study_session.id
            for study_session in current_user.joined + current_user.saved + current_user.hosted_sessions
        }
        sessions = StudySession.query.filter(StudySession.id.in_(ids)).all() if ids else []

    return render_template(
        "my_sessions.html",
        sessions=sessions,
        current_view=view,
    )


# ---------- Session Detail ----------
@main.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
    current_user = get_current_user()
    study_session = StudySession.query.get_or_404(session_id)

    messages = (
        SessionMessage.query
        .filter_by(
            session_id=study_session.id,
            parent_id=None,
        )
        .order_by(SessionMessage.created_at.desc())
        .all()
    )

    joined_ids = {user.id for user in study_session.joined_users}
    is_joined = current_user.id in joined_ids

    if is_joined:
        mark_session_messages_read(current_user, study_session.id)

    return render_template(
        "session_detail.html",
        session=study_session,
        messages=messages,
        current_user=current_user,
        is_joined=is_joined,
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
            content=content,
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
            content=content,
        )

        db.session.add(reply)
        db.session.commit()

    return redirect(url_for("main.session_detail", session_id=session_id))

# ---------- Activity Grid ----------
def build_profile_activity_grid(user_posts, user_comments, hosted_sessions, joined_sessions):
    year = date.today().year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    activity_counts = defaultdict(int)

    summary = {
        "posts": 0,
        "comments": 0,
        "created_sessions": 0,
        "joined_sessions": 0,
    }

    def normalise_date(value):
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        return value

    def add_activity(value, activity_type):
        activity_date = normalise_date(value)

        if activity_date is None:
            return

        # Count the whole current year, not only up to today.
        if start_date <= activity_date <= end_date:
            activity_counts[activity_date] += 1
            summary[activity_type] += 1

    for thread in user_posts:
        add_activity(thread.created_at, "posts")

    for reply in user_comments:
        add_activity(reply.created_at, "comments")

    # StudySession has no created_at, so session_date is used.
    for study_session in hosted_sessions:
        add_activity(study_session.session_date, "created_sessions")

    # joined_sessions has no joined_at timestamp, so session_date is used.
    for study_session in joined_sessions:
        add_activity(study_session.session_date, "joined_sessions")

    days = []
    current_day = start_date

    while current_day <= end_date:
        count = activity_counts[current_day]

        if count == 0:
            level = 0
        elif count == 1:
            level = 1
        elif count == 2:
            level = 2
        elif count <= 4:
            level = 3
        else:
            level = 4

        days.append({
            "date": current_day,
            "count": count,
            "level": level,
        })

        current_day += timedelta(days=1)

    leading_blanks = start_date.weekday()
    padded_days = [None] * leading_blanks + days

    weeks = []

    for index in range(0, len(padded_days), 7):
        week = padded_days[index:index + 7]

        while len(week) < 7:
            week.append(None)

        weeks.append(week)

    month_header_weeks = []

    for week in weeks:
        label = ""

        for day in week:
            if day and day["date"].day == 1:
                label = day["date"].strftime("%b")
                break

        month_header_weeks.append(label)

    return {
        "year": year,
        "weeks": weeks,
        "month_header_weeks": month_header_weeks,
        "total": sum(activity_counts.values()),
        "summary": summary,
    }

def build_profile_overview_context(profile_user):
    user_posts = sorted(
        profile_user.forum_threads,
        key=lambda thread: (
            thread.created_at or datetime.min,
            thread.id,
        ),
        reverse=True,
    )

    user_comments = sorted(
        profile_user.forum_replies,
        key=lambda reply: (
            reply.created_at or datetime.min,
            reply.id,
        ),
        reverse=True,
    )

    hosted_sessions = sorted(
        profile_user.hosted_sessions,
        key=lambda study_session: (
            study_session.session_date or date.min,
            study_session.id,
        ),
        reverse=True,
    )

    hosted_session_ids = {study_session.id for study_session in hosted_sessions}

    joined_sessions = [
        study_session
        for study_session in profile_user.joined
        if study_session.id not in hosted_session_ids
    ]

    joined_sessions = sorted(
        joined_sessions,
        key=lambda study_session: (
            study_session.session_date or date.min,
            study_session.id,
        ),
        reverse=True,
    )

    activity_grid = build_profile_activity_grid(
        user_posts,
        user_comments,
        hosted_sessions,
        joined_sessions,
    )

    return {
        "profile_user": profile_user,
        "activity_grid": activity_grid,
        "post_count": len(user_posts),
        "comment_count": len(user_comments),
        "hosted_count": len(hosted_sessions),
        "joined_count": len(joined_sessions),
    }


# ---------- Profile ----------
@main.route("/profile")
@login_required
def profile():
    current_user = get_current_user()

    active_tab = request.args.get("tab", "overview")
    valid_tabs = {"overview", "posts", "comments", "saved", "studybuddy"}

    if active_tab not in valid_tabs:
        active_tab = "overview"

    saved_filter = request.args.get("saved", "all")
    valid_saved_filters = {"all", "posts", "sessions"}

    if saved_filter not in valid_saved_filters:
        saved_filter = "all"

    studybuddy_filter = request.args.get("studybuddy", "all")
    valid_studybuddy_filters = {"all", "hosted", "joined"}

    if studybuddy_filter not in valid_studybuddy_filters:
        studybuddy_filter = "all"

    user_posts = (
        ForumThread.query
        .filter_by(author_id=current_user.id)
        .order_by(ForumThread.created_at.desc(), ForumThread.id.desc())
        .all()
    )

    user_comments = (
        ForumReply.query
        .filter_by(author_id=current_user.id)
        .order_by(ForumReply.created_at.desc(), ForumReply.id.desc())
        .all()
    )

    hosted_sessions = (
        StudySession.query
        .filter_by(host_id=current_user.id)
        .order_by(StudySession.session_date.desc(), StudySession.id.desc())
        .all()
    )

    hosted_session_ids = {study_session.id for study_session in hosted_sessions}

    joined_sessions = [
        study_session
        for study_session in current_user.joined
        if study_session.id not in hosted_session_ids
    ]

    joined_sessions = sorted(
        joined_sessions,
        key=lambda study_session: (
            study_session.session_date or date.min,
            study_session.id,
        ),
        reverse=True,
    )

    activity_grid = build_profile_activity_grid(
        user_posts,
        user_comments,
        hosted_sessions,
        joined_sessions,
    )

    saved_forum_threads = sorted(
        current_user.saved_forum_threads,
        key=lambda thread: (
            thread.created_at or datetime.min,
            thread.id,
        ),
        reverse=True,
    )

    saved_sessions = sorted(
        current_user.saved,
        key=lambda study_session: (
            study_session.session_date or date.min,
            study_session.id,
        ),
        reverse=True,
    )

    saved_items = []

    if saved_filter in {"all", "posts"}:
        for thread in saved_forum_threads:
            saved_items.append({
                "kind": "post",
                "thread": thread,
                "sort_date": thread.created_at or datetime.min,
            })

    if saved_filter in {"all", "sessions"}:
        for study_session in saved_sessions:
            session_datetime = (
                datetime.combine(study_session.session_date, datetime.min.time())
                if study_session.session_date
                else datetime.min
            )

            saved_items.append({
                "kind": "session",
                "session": study_session,
                "sort_date": session_datetime,
            })

    saved_items.sort(
        key=lambda item: item["sort_date"],
        reverse=True,
    )

    studybuddy_items = []

    if studybuddy_filter in {"all", "hosted"}:
        for study_session in hosted_sessions:
            studybuddy_items.append({
                "role": "Hosted",
                "initial": "H",
                "session": study_session,
            })

    if studybuddy_filter in {"all", "joined"}:
        for study_session in joined_sessions:
            studybuddy_items.append({
                "role": "Joined",
                "initial": "J",
                "session": study_session,
            })

    studybuddy_items.sort(
        key=lambda item: (
            item["session"].session_date or date.min,
            item["session"].id,
        ),
        reverse=True,
    )

    recent_activity = []

    for thread in user_posts[:3]:
        recent_activity.append({
            "type": "Forum",
            "title": thread.title,
            "meta": f"{thread.like_count} likes · {thread.reply_count} comments",
            "url": url_for("main.thread_detail", thread_id=thread.id),
            "created_at": thread.created_at or datetime.min,
            "initial": "F",
        })

    for reply in user_comments[:3]:
        reply_preview = reply.body[:120]

        if len(reply.body) > 120:
            reply_preview += "..."

        recent_activity.append({
            "type": "Comment",
            "title": reply.thread.title if reply.thread else "Forum comment",
            "meta": reply_preview,
            "url": url_for("main.thread_detail", thread_id=reply.thread_id),
            "created_at": reply.created_at or datetime.min,
            "initial": "C",
        })

    for study_session in hosted_sessions[:3]:
        session_datetime = (
            datetime.combine(study_session.session_date, datetime.min.time())
            if study_session.session_date
            else datetime.min
        )

        session_date_label = (
            study_session.session_date.strftime("%d %b %Y")
            if study_session.session_date
            else "Date TBA"
        )

        recent_activity.append({
            "type": "Study Buddy",
            "title": study_session.topic,
            "meta": f"{study_session.unit_code} · {session_date_label}",
            "url": url_for("main.session_detail", session_id=study_session.id),
            "created_at": session_datetime,
            "initial": "S",
        })

    recent_activity.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return render_template(
        "profile.html",
        current_user=current_user,
        active_tab=active_tab,
        saved_filter=saved_filter,
        studybuddy_filter=studybuddy_filter,
        user_posts=user_posts,
        user_comments=user_comments,
        hosted_sessions=hosted_sessions,
        joined_sessions=joined_sessions,
        saved_forum_threads=saved_forum_threads,
        saved_sessions=saved_sessions,
        saved_items=saved_items,
        studybuddy_items=studybuddy_items,
        recent_activity=recent_activity[:6],
        post_count=len(user_posts),
        comment_count=len(user_comments),
        hosted_count=len(hosted_sessions),
        joined_count=len(joined_sessions),
        activity_grid=activity_grid,
    )


@main.route("/users/<int:user_id>")
@login_required
def public_profile(user_id):
    viewer = get_current_user()

    if viewer is None:
        return redirect(url_for("auth.login"))

    profile_user = db.session.get(User, user_id)

    if profile_user is None:
        abort(404)

    if profile_user.id == viewer.id:
        return redirect(url_for("main.profile"))

    profile_context = build_profile_overview_context(profile_user)

    return render_template(
        "public_profile.html",
        **profile_context,
    )