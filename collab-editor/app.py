from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify
)

from flask_socketio import (
    SocketIO,
    emit,
    join_room,
    leave_room
)

import uuid
import threading
import time

import db

# =====================================================
# Flask Configuration
# =====================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "collab_editor_secret_key"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# =====================================================
# In-Memory Cache
# =====================================================

documents = {}

save_timers = {}

user_counts = {}

DEFAULT_LANGUAGE = "python"

SAVE_DELAY = 2.0
# =====================================================
# Database Helper
# =====================================================

def db_safe(func, *args, fallback=None):
    """
    Executes database functions safely.

    If PostgreSQL is unavailable,
    the application continues running.
    """

    try:
        return func(*args)

    except Exception as e:

        print(f"[DATABASE ERROR] {e}")

        return fallback
    # =====================================================
# Auto Save
# =====================================================

def schedule_save(room_id):
    """
    Save document after user stops typing.
    """

    if room_id not in documents:
        return

    if room_id in save_timers:
        save_timers[room_id].cancel()

    def save():

        code = documents.get(room_id, "")

        db_safe(
            db.save_document_content,
            room_id,
            code
        )

        print(f"Saved room {room_id}")

    timer = threading.Timer(
        SAVE_DELAY,
        save
    )

    save_timers[room_id] = timer

    timer.start()
    # =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    """
    Landing Page
    """

    return render_template("home.html")


# =====================================================
# CREATE NEW ROOM
# =====================================================

@app.route("/new-room")
def new_room():

    room_id = str(uuid.uuid4())[:8]

    # Create room inside PostgreSQL
    db_safe(
        db.ensure_room,
        room_id,
        DEFAULT_LANGUAGE
    )

    # Load existing document if any
    code = db_safe(
        db.get_document_content,
        room_id,
        fallback=""
    )

    documents[room_id] = code

    return redirect(
        url_for(
            "editor",
            room_id=room_id
        )
    )


# =====================================================
# JOIN EXISTING ROOM
# =====================================================

@app.route("/join", methods=["POST"])
def join_existing():

    room_id = request.form.get("room_id", "").strip()

    if room_id == "":

        return redirect(url_for("home"))

    # Create room automatically if it doesn't exist
    db_safe(
        db.ensure_room,
        room_id,
        DEFAULT_LANGUAGE
    )

    return redirect(
        url_for(
            "editor",
            room_id=room_id
        )
    )


# =====================================================
# EDITOR
# =====================================================

@app.route("/editor/<room_id>")
def editor(room_id):

    # Make sure room exists
    db_safe(
        db.ensure_room,
        room_id,
        DEFAULT_LANGUAGE
    )

    language = db_safe(
        db.get_room_language,
        room_id,
        fallback=DEFAULT_LANGUAGE
    )

    code = db_safe(
        db.get_document_content,
        room_id,
        fallback=""
    )

    documents[room_id] = code

    return render_template(
        "editor.html",
        room_id=room_id,
        language=language,
        code=code
    )


# =====================================================
# API
# =====================================================

@app.route("/api/room/<room_id>")
def room_details(room_id):

    return jsonify({

        "room_id": room_id,

        "language": db_safe(
            db.get_room_language,
            room_id,
            fallback="python"
        ),

        "content": db_safe(
            db.get_document_content,
            room_id,
            fallback=""
        )

    })


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")
def health():

    connected = db.test_connection()

    return jsonify({

        "database": connected,

        "status": "Running"

    })
# =====================================================
# SOCKET EVENTS
# =====================================================

@socketio.on("join")
def handle_join(data):
    """
    User joins a collaboration room.
    """

    room_id = data.get("room")
    username = data.get("username", "Guest")

    if not room_id:
        return

    join_room(room_id)

    # Track online users
    if room_id not in user_counts:
        user_counts[room_id] = 0

    user_counts[room_id] += 1

    # Save session
    db_safe(
        db.user_join,
        room_id,
        username
    )

    # Load document from DB if not cached
    if room_id not in documents:

        documents[room_id] = db_safe(
            db.get_document_content,
            room_id,
            fallback=""
        )

    # Send existing code to newly joined user
    emit(
        "load_code",
        {
            "code": documents[room_id]
        },
        room=request.sid
    )

    # Notify everyone
    emit(
        "user_joined",
        {
            "username": username,
            "users": user_counts[room_id]
        },
        room=room_id
    )

    print(f"{username} joined {room_id}")


# =====================================================
# CODE UPDATE
# =====================================================

@socketio.on("code_change")
def handle_code_change(data):

    room_id = data.get("room")
    code = data.get("code", "")

    if not room_id:
        return

    documents[room_id] = code

    schedule_save(room_id)

    emit(
        "code_update",
        {
            "code": code
        },
        room=room_id,
        include_self=False
    )


# =====================================================
# LANGUAGE CHANGE
# =====================================================

@socketio.on("language_change")
def handle_language_change(data):

    room_id = data.get("room")
    language = data.get("language")

    if not room_id:
        return

    db_safe(
        db.set_room_language,
        room_id,
        language
    )

    emit(
        "language_update",
        {
            "language": language
        },
        room=room_id,
        include_self=False
    )

    print(f"Language changed to {language}")


# =====================================================
# SAVE DOCUMENT
# =====================================================

@socketio.on("save_document")
def handle_manual_save(data):

    room_id = data.get("room")

    if not room_id:
        return

    code = documents.get(room_id, "")

    db_safe(
        db.save_document_content,
        room_id,
        code
    )

    emit(
        "saved",
        {
            "success": True
        },
        room=request.sid
    )

    print(f"Manual save completed for {room_id}")


# =====================================================
# USER LEAVE
# =====================================================

@socketio.on("leave")
def handle_leave(data):

    room_id = data.get("room")
    username = data.get("username", "Guest")

    if not room_id:
        return

    leave_room(room_id)

    db_safe(
        db.user_leave,
        room_id,
        username
    )

    if room_id in user_counts:

        user_counts[room_id] -= 1

        if user_counts[room_id] < 0:
            user_counts[room_id] = 0

    emit(
        "user_left",
        {
            "username": username,
            "users": user_counts.get(room_id, 0)
        },
        room=room_id
    )

    print(f"{username} left {room_id}")


# =====================================================
# DISCONNECT
# =====================================================

@socketio.on("disconnect")
def handle_disconnect():

    print("Client disconnected.")
    # =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def page_not_found(error):
    return (
        render_template(
            "404.html",
            message="The page you are looking for does not exist."
        ),
        404,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        render_template(
            "500.html",
            message="Something went wrong on the server."
        ),
        500,
    )


# =====================================================
# STARTUP
# =====================================================

def initialize_database():
    """
    Verify PostgreSQL connection when the application starts.
    """

    print("\n========================================")
    print("     CodeCollab Pro")
    print("========================================")

    if db.test_connection():
        print("✓ PostgreSQL Connected")
    else:
        print("✗ PostgreSQL Connection Failed")

    print("✓ Flask Server Ready")
    print("========================================\n")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    initialize_database()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )