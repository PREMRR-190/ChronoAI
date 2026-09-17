import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


# ==================================================
# FLASK
# ==================================================

app = Flask(__name__)


# ==================================================
# SECRET KEY
# ==================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    os.environ.get(
        "CHRONOAI_SECRET_KEY",
        "chronoai-dev-secret-change-me"
    )
)

app.secret_key = SECRET_KEY


# ==================================================
# FRONTEND URL
# ==================================================

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "http://localhost:5173"
).rstrip("/")


# ==================================================
# PRODUCTION
# ==================================================

PRODUCTION = (
    os.environ.get("PRODUCTION", "false").lower() == "true"
)


# ==================================================
# CORS
# ==================================================

allowed_origins = [
    FRONTEND_URL,
    "https://chronoai-orcin.vercel.app",
    "https://chronoai-atf468m0i-prem-f4e7.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Remove duplicate origins
allowed_origins = list(set(allowed_origins))


CORS(
    app,
    resources={
        r"/api/*": {
            "origins": allowed_origins
        }
    },
    supports_credentials=True
)


# ==================================================
# SESSION COOKIE
# ==================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SECURE"] = PRODUCTION

app.config["SESSION_COOKIE_SAMESITE"] = (
    "None" if PRODUCTION else "Lax"
)

app.config["SESSION_COOKIE_PATH"] = "/"

app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30


# ==================================================
# MONGODB
# ==================================================

# Render will provide MONGO_URI
# Local computer will use localhost if MONGO_URI is not set

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017/"
)


client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)


db = client["ChronoAI"]


# ==================================================
# COLLECTIONS
# ==================================================

users_collection = db["users"]

tasks_collection = db["tasks"]

schedule_collection = db["schedules"]

habits_collection = db["daily_habits"]


# ==================================================
# USERNAME INDEX
# ==================================================

# Prevent duplicate usernames in MongoDB

try:
    users_collection.create_index(
        "username",
        unique=True
    )
except Exception:
    pass


# ==================================================
# HELPERS
# ==================================================

def current_user_id():
    return session.get("user_id")


def login_required():
    if not current_user_id():
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    return None


def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "username": user["username"]
    }


def object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def utc_now():
    return datetime.now(timezone.utc)


# ==================================================
# HOME
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "ChronoAI Backend is running!",
        "login_system": True
    })


# ==================================================
# HEALTH CHECK
# ==================================================

@app.route("/api/health", methods=["GET"])
def health():

    try:

        # Test MongoDB connection
        client.admin.command("ping")

        return jsonify({
            "success": True,
            "flask": True,
            "mongodb": True,
            "message": "ChronoAI API and MongoDB are working"
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "flask": True,
            "mongodb": False,
            "message": str(e)
        }), 500


# ==================================================
# REGISTER
# ==================================================

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json(silent=True) or {}

        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        # ------------------------------
        # VALIDATION
        # ------------------------------

        if len(username) < 3:

            return jsonify({
                "success": False,
                "message": "Username must be at least 3 characters"
            }), 400


        if len(password) < 6:

            return jsonify({
                "success": False,
                "message": "Password must be at least 6 characters"
            }), 400


        # ------------------------------
        # CHECK EXISTING USER
        # ------------------------------

        existing_user = users_collection.find_one({
            "username": username
        })


        if existing_user:

            return jsonify({
                "success": False,
                "message": "Username already exists"
            }), 409


        # ------------------------------
        # CREATE USER
        # ------------------------------

        hashed_password = generate_password_hash(
            password
        )


        user = {
            "username": username,
            "password": hashed_password,
            "created_at": utc_now()
        }


        result = users_collection.insert_one(user)

        user["_id"] = result.inserted_id


        # ------------------------------
        # AUTO LOGIN
        # ------------------------------

        session.clear()

        session["user_id"] = str(
            result.inserted_id
        )

        session["username"] = username

        session.permanent = True


        return jsonify({

            "success": True,

            "message": "Account created successfully",

            "user": serialize_user(user)

        }), 201


    except Exception as e:

        return jsonify({

            "success": False,

            "message": f"Registration failed: {str(e)}"

        }), 500


# ==================================================
# LOGIN
# ==================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json(silent=True) or {}

        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        # ------------------------------
        # VALIDATION
        # ------------------------------

        if not username or not password:

            return jsonify({

                "success": False,

                "message":
                    "Username and password are required"

            }), 400


        # ------------------------------
        # FIND USER
        # ------------------------------

        user = users_collection.find_one({
            "username": username
        })


        # ------------------------------
        # CHECK PASSWORD
        # ------------------------------

        if not user:

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password"

            }), 401


        stored_password = user.get(
            "password",
            ""
        )


        if not check_password_hash(
            stored_password,
            password
        ):

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password"

            }), 401


        # ------------------------------
        # CREATE SESSION
        # ------------------------------

        session.clear()

        session["user_id"] = str(
            user["_id"]
        )

        session["username"] = user["username"]

        session.permanent = True


        return jsonify({

            "success": True,

            "message": "Login successful",

            "user": serialize_user(user)

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": f"Login failed: {str(e)}"

        }), 500


# ==================================================
# CURRENT USER
# ==================================================

@app.route("/api/me", methods=["GET"])
def me():

    try:

        user_id = current_user_id()


        if not user_id:

            return jsonify({

                "success": False,
                "user": None

            }), 401


        oid = object_id(user_id)


        if oid is None:

            session.clear()

            return jsonify({

                "success": False,
                "user": None

            }), 401


        user = users_collection.find_one({
            "_id": oid
        })


        if not user:

            session.clear()

            return jsonify({

                "success": False,
                "user": None

            }), 401


        return jsonify({

            "success": True,

            "user": serialize_user(user)

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==================================================
# LOGOUT
# ==================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({

        "success": True,

        "message": "Logged out successfully"

    }), 200


# ==================================================
# TEST AUTH
# ==================================================

@app.route("/api/test-auth", methods=["GET"])
def test_auth():

    user_id = current_user_id()


    if not user_id:

        return jsonify({

            "success": False,

            "logged_in": False

        }), 401


    return jsonify({

        "success": True,

        "logged_in": True,

        "username":
            session.get("username")

    }), 200


# ==================================================
# TASKS
# ==================================================

@app.route("/api/tasks", methods=["POST"])
def add_task():

    auth = login_required()

    if auth:
        return auth


    try:

        data = request.get_json(silent=True) or {}


        title = str(
            data.get("title", "")
        ).strip()


        priority = str(
            data.get("priority", "Medium")
        )


        hours = data.get(
            "hours",
            1
        )


        if not title:

            return jsonify({

                "success": False,

                "message":
                    "Task title is required"

            }), 400


        # Validate hours

        try:
            hours = float(hours)

        except (TypeError, ValueError):

            return jsonify({

                "success": False,

                "message":
                    "Hours must be a number"

            }), 400


        task = {

            # Every task belongs to one user
            "user_id":
                current_user_id(),

            "title":
                title,

            "priority":
                priority,

            "hours":
                hours,

            "completed":
                False,

            "created_at":
                utc_now()
        }


        result = tasks_collection.insert_one(task)


        return jsonify({

            "success": True,

            "task": {

                "id":
                    str(result.inserted_id),

                "title":
                    title,

                "priority":
                    priority,

                "hours":
                    hours,

                "completed":
                    False

            }

        }), 201


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# GET TASKS
# ==================================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    auth = login_required()

    if auth:
        return auth


    try:

        tasks = list(

            tasks_collection.find({

                "user_id":
                    current_user_id()

            }).sort(

                "created_at",
                -1

            )

        )


        result = []


        for task in tasks:

            result.append({

                "id":
                    str(task["_id"]),

                "title":
                    task.get(
                        "title",
                        ""
                    ),

                "priority":
                    task.get(
                        "priority",
                        "Medium"
                    ),

                "hours":
                    task.get(
                        "hours",
                        1
                    ),

                "completed":
                    task.get(
                        "completed",
                        False
                    )

            })


        return jsonify({

            "success": True,

            "tasks":
                result

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# UPDATE TASK
# ==================================================

@app.route(
    "/api/tasks/<task_id>",
    methods=["PUT"]
)
def update_task(task_id):

    auth = login_required()

    if auth:
        return auth


    oid = object_id(task_id)


    if oid is None:

        return jsonify({

            "success": False,

            "message":
                "Invalid task ID"

        }), 400


    try:

        data = request.get_json(
            silent=True
        ) or {}


        completed = bool(
            data.get(
                "completed",
                False
            )
        )


        result = tasks_collection.update_one(

            {
                "_id": oid,
                "user_id":
                    current_user_id()
            },

            {
                "$set": {
                    "completed":
                        completed
                }
            }

        )


        if result.matched_count == 0:

            return jsonify({

                "success": False,

                "message":
                    "Task not found"

            }), 404


        return jsonify({

            "success": True,

            "message":
                "Task updated successfully"

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# DELETE TASK
# ==================================================

@app.route(
    "/api/tasks/<task_id>",
    methods=["DELETE"]
)
def delete_task(task_id):

    auth = login_required()

    if auth:
        return auth


    oid = object_id(task_id)


    if oid is None:

        return jsonify({

            "success": False,

            "message":
                "Invalid task ID"

        }), 400


    try:

        result = tasks_collection.delete_one({

            "_id": oid,

            "user_id":
                current_user_id()

        })


        if result.deleted_count == 0:

            return jsonify({

                "success": False,

                "message":
                    "Task not found"

            }), 404


        return jsonify({

            "success": True,

            "message":
                "Task deleted successfully"

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# SCHEDULE
# ==================================================

@app.route(
    "/api/schedule",
    methods=["POST"]
)
def add_schedule():

    auth = login_required()

    if auth:
        return auth


    try:

        data = request.get_json(
            silent=True
        ) or {}


        time = str(
            data.get("time", "")
        ).strip()


        activity = str(
            data.get("activity", "")
        ).strip()


        if not time or not activity:

            return jsonify({

                "success": False,

                "message":
                    "Time and activity are required"

            }), 400


        schedule = {

            "user_id":
                current_user_id(),

            "time":
                time,

            "activity":
                activity,

            "created_at":
                utc_now()

        }


        result = schedule_collection.insert_one(
            schedule
        )


        return jsonify({

            "success": True,

            "schedule": {

                "id":
                    str(result.inserted_id),

                "time":
                    time,

                "activity":
                    activity

            }

        }), 201


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# GET SCHEDULE
# ==================================================

@app.route(
    "/api/schedule",
    methods=["GET"]
)
def get_schedule():

    auth = login_required()

    if auth:
        return auth


    try:

        schedules = list(

            schedule_collection.find({

                "user_id":
                    current_user_id()

            }).sort(

                "created_at",
                1

            )

        )


        result = []


        for item in schedules:

            result.append({

                "id":
                    str(item["_id"]),

                "time":
                    item.get(
                        "time",
                        ""
                    ),

                "activity":
                    item.get(
                        "activity",
                        ""
                    )

            })


        return jsonify({

            "success": True,

            "schedule":
                result

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# DELETE SCHEDULE
# ==================================================

@app.route(
    "/api/schedule/<schedule_id>",
    methods=["DELETE"]
)
def delete_schedule(schedule_id):

    auth = login_required()

    if auth:
        return auth


    oid = object_id(schedule_id)


    if oid is None:

        return jsonify({

            "success": False,

            "message":
                "Invalid schedule ID"

        }), 400


    try:

        result = schedule_collection.delete_one({

            "_id": oid,

            "user_id":
                current_user_id()

        })


        if result.deleted_count == 0:

            return jsonify({

                "success": False,

                "message":
                    "Schedule not found"

            }), 404


        return jsonify({

            "success": True,

            "message":
                "Schedule deleted successfully"

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# DAILY HABITS
# ==================================================

@app.route(
    "/api/habits",
    methods=["POST"]
)
def save_habits():

    auth = login_required()

    if auth:
        return auth


    try:

        data = request.get_json(
            silent=True
        ) or {}


        sleep_time = str(
            data.get(
                "sleep_time",
                ""
            )
        ).strip()


        wake_time = str(
            data.get(
                "wake_time",
                ""
            )
        ).strip()


        screen_time = data.get(
            "screen_time",
            0
        )


        study_time = data.get(
            "study_time",
            0
        )


        if not sleep_time or not wake_time:

            return jsonify({

                "success": False,

                "message":
                    "Sleep and wake-up time are required"

            }), 400


        try:

            screen_time = float(screen_time)
            study_time = float(study_time)

        except (TypeError, ValueError):

            return jsonify({

                "success": False,

                "message":
                    "Screen time and study time must be numbers"

            }), 400


        habit = {

            "user_id":
                current_user_id(),

            "sleep_time":
                sleep_time,

            "wake_time":
                wake_time,

            "screen_time":
                screen_time,

            "study_time":
                study_time,

            "created_at":
                utc_now()

        }


        result = habits_collection.insert_one(
            habit
        )


        return jsonify({

            "success": True,

            "message":
                "Daily habits saved successfully",

            "habit": {

                "id":
                    str(result.inserted_id),

                "sleep_time":
                    sleep_time,

                "wake_time":
                    wake_time,

                "screen_time":
                    screen_time,

                "study_time":
                    study_time

            }

        }), 201


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# GET HABITS
# ==================================================

@app.route(
    "/api/habits",
    methods=["GET"]
)
def get_habits():

    auth = login_required()

    if auth:
        return auth


    try:

        habit = habits_collection.find_one(

            {
                "user_id":
                    current_user_id()
            },

            sort=[
                (
                    "created_at",
                    -1
                )
            ]

        )


        if not habit:

            return jsonify({

                "success": True,

                "habit": None

            }), 200


        return jsonify({

            "success": True,

            "habit": {

                "id":
                    str(habit["_id"]),

                "sleep_time":
                    habit.get(
                        "sleep_time",
                        ""
                    ),

                "wake_time":
                    habit.get(
                        "wake_time",
                        ""
                    ),

                "screen_time":
                    habit.get(
                        "screen_time",
                        0
                    ),

                "study_time":
                    habit.get(
                        "study_time",
                        0
                    )

            }

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    print()
    print("====================================")
    print("       ChronoAI Backend Server")
    print("====================================")
    print(f"Frontend  : {FRONTEND_URL}")
    print(f"Production: {PRODUCTION}")
    print("Database  : ChronoAI")
    print("====================================")
    print()


    app.run(
        host="0.0.0.0",
        port=port,
        debug=not PRODUCTION
    )