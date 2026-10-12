import os
import json
import re
from datetime import datetime, timezone

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from upstash_redis import Redis
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

if os.environ.get("RENDER", "").lower() == "true" and SECRET_KEY == "chronoai-dev-secret-change-me":
    app.logger.warning(
        "SECRET_KEY is using the development fallback. Set a private SECRET_KEY in Render."
    )


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

# Render deployments should use secure cross-site cookies by default.
# You can explicitly override this with PRODUCTION=true/false in Render.
production_default = "true" if os.environ.get("RENDER", "").lower() == "true" else "false"
PRODUCTION = os.environ.get("PRODUCTION", production_default).lower() == "true"


# ==================================================
# CORS
# ==================================================

# Keep the stable production alias and allow this project's unique Vercel
# deployment URLs too (for example: chronoai-<deployment>-prem-f4e7.vercel.app).
# The pattern is restricted to HTTPS origins whose Vercel hostname starts with
# "chronoai", rather than allowing every *.vercel.app site.
vercel_chronoai_origin = re.compile(
    r"^https://chronoai(?:-[a-z0-9-]+)?\.vercel\.app$",
    re.IGNORECASE
)

allowed_origins = [
    FRONTEND_URL,
    "https://chronoai-orcin.vercel.app",
    "https://chronoai-atf468m0i-prem-f4e7.vercel.app",
    "https://chronoai-2zouz15jz-prem-f4e7.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    vercel_chronoai_origin,
]

# Remove duplicate string origins while retaining the compiled regex.
allowed_origins = list(dict.fromkeys(
    origin for origin in allowed_origins if isinstance(origin, str)
)) + [vercel_chronoai_origin]


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
# REDIS (UPSTASH)
# ==================================================
# Configure these in Render Environment. Never hardcode the token.

UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

redis_client = None

if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    redis_client = Redis(
        url=UPSTASH_REDIS_REST_URL,
        token=UPSTASH_REDIS_REST_TOKEN
    )


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


def task_to_api_dict(task):
    """Convert a MongoDB task document into the format used by React/Redis."""
    return {
        "id": str(task["_id"]),
        "title": task.get("title", ""),
        "priority": task.get("priority", "Medium"),
        "hours": task.get("hours", 1),
        "completed": task.get("completed", False),
    }


def redis_tasks_key(user_id):
    """Use a separate Redis key for every user."""
    return f"chronoai:user:{user_id}:tasks"


def sync_user_tasks_to_redis(user_id):
    """Mirror one user's current MongoDB tasks into Redis as a JSON array.

    MongoDB remains the permanent source of truth. The Redis mirror is refreshed
    after task create/update/delete and when the frontend loads task data.
    """
    if redis_client is None:
        app.logger.warning("Redis is not configured; task mirror was not updated")
        return False

    try:
        documents = list(
            tasks_collection.find({"user_id": str(user_id)}).sort("created_at", -1)
        )
        payload = [task_to_api_dict(task) for task in documents]
        redis_client.set(
            redis_tasks_key(user_id),
            json.dumps(payload, separators=(",", ":"))
        )
        return True
    except Exception:
        app.logger.exception("Could not sync tasks to Redis for user %s", user_id)
        return False


def redis_schedules_key(user_id):
    """A separate Redis list for each logged-in user's schedules."""
    return f"chronoai:user:{user_id}:schedules"


def redis_habits_key(user_id):
    """A separate Redis list for each logged-in user's saved habit history."""
    return f"chronoai:user:{user_id}:habits"


def schedule_to_api_dict(item):
    return {
        "id": str(item["_id"]),
        "time": item.get("time", ""),
        "activity": item.get("activity", ""),
    }


def habit_to_redis_dict(habit):
    created_at = habit.get("created_at")
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    elif created_at is not None:
        created_at = str(created_at)

    return {
        "id": str(habit["_id"]),
        "sleep_time": habit.get("sleep_time", ""),
        "wake_time": habit.get("wake_time", ""),
        "screen_time": habit.get("screen_time", 0),
        "study_time": habit.get("study_time", 0),
        "created_at": created_at,
    }


def sync_user_schedules_to_redis(user_id):
    """Mirror every schedule belonging to this user; MongoDB is authoritative."""
    if redis_client is None:
        return False

    try:
        documents = list(
            schedule_collection.find({"user_id": str(user_id)}).sort("created_at", 1)
        )
        payload = [schedule_to_api_dict(item) for item in documents]
        redis_client.set(
            redis_schedules_key(user_id),
            json.dumps(payload, separators=(",", ":"))
        )
        return True
    except Exception:
        app.logger.exception("Could not sync schedules to Redis for user %s", user_id)
        return False


def sync_user_habits_to_redis(user_id):
    """Mirror all saved habit records belonging to this user."""
    if redis_client is None:
        return False

    try:
        documents = list(
            habits_collection.find({"user_id": str(user_id)}).sort("created_at", -1)
        )
        payload = [habit_to_redis_dict(item) for item in documents]
        redis_client.set(
            redis_habits_key(user_id),
            json.dumps(payload, separators=(",", ":"))
        )
        return True
    except Exception:
        app.logger.exception("Could not sync habits to Redis for user %s", user_id)
        return False


def sync_all_user_data_to_redis(user_id):
    """Create/refresh this user's task, schedule, and habit mirrors in Redis.

    This runs on login/registration and the individual endpoints also refresh
    the corresponding mirror after changes. User accounts/password hashes stay
    in MongoDB and are deliberately not copied to Redis.
    """
    return {
        "tasks": sync_user_tasks_to_redis(user_id),
        "schedules": sync_user_schedules_to_redis(user_id),
        "habits": sync_user_habits_to_redis(user_id),
    }


def read_redis_json(key, fallback):
    """Read and parse a JSON value saved by one of the sync helpers."""
    raw_value = redis_client.get(key)
    if raw_value is None:
        return fallback
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")
    return json.loads(raw_value) if isinstance(raw_value, str) else raw_value


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

        redis_sync = sync_all_user_data_to_redis(session["user_id"])

        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": serialize_user(user),
            "redis_synced": all(redis_sync.values()),
            "redis_sync": redis_sync,
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

        redis_sync = sync_all_user_data_to_redis(session["user_id"])

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": serialize_user(user),
            "redis_synced": all(redis_sync.values()),
            "redis_sync": redis_sync,
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
# TASKS — MONGODB + REDIS MIRROR
# ==================================================

@app.route("/api/tasks", methods=["POST"])
def add_task():
    auth = login_required()
    if auth:
        return auth

    try:
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        priority = str(data.get("priority", "Medium"))
        hours = data.get("hours", 1)

        if not title:
            return jsonify({
                "success": False,
                "message": "Task title is required"
            }), 400

        try:
            hours = float(hours)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Hours must be a number"
            }), 400

        task = {
            "user_id": str(current_user_id()),
            "title": title,
            "priority": priority,
            "hours": hours,
            "completed": False,
            "created_at": utc_now(),
        }

        result = tasks_collection.insert_one(task)
        task["_id"] = result.inserted_id
        redis_synced = sync_user_tasks_to_redis(current_user_id())

        return jsonify({
            "success": True,
            "message": (
                "Task saved to MongoDB and Redis"
                if redis_synced
                else "Task saved to MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
            "task": task_to_api_dict(task),
        }), 201

    except Exception as e:
        app.logger.exception("Could not add task")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    auth = login_required()
    if auth:
        return auth

    try:
        documents = list(
            tasks_collection.find({"user_id": str(current_user_id())})
            .sort("created_at", -1)
        )
        result = [task_to_api_dict(task) for task in documents]
        # Refresh Redis from MongoDB so existing tasks are mirrored after login.
        redis_synced = sync_user_tasks_to_redis(current_user_id())

        return jsonify({
            "success": True,
            "tasks": result,
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not load tasks")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    auth = login_required()
    if auth:
        return auth

    oid = object_id(task_id)
    if oid is None:
        return jsonify({"success": False, "message": "Invalid task ID"}), 400

    try:
        data = request.get_json(silent=True) or {}
        completed = bool(data.get("completed", False))

        result = tasks_collection.update_one(
            {"_id": oid, "user_id": str(current_user_id())},
            {"$set": {"completed": completed}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Task not found"}), 404

        redis_synced = sync_user_tasks_to_redis(current_user_id())
        return jsonify({
            "success": True,
            "message": (
                "Task updated in MongoDB and Redis"
                if redis_synced
                else "Task updated in MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not update task")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    auth = login_required()
    if auth:
        return auth

    oid = object_id(task_id)
    if oid is None:
        return jsonify({"success": False, "message": "Invalid task ID"}), 400

    try:
        result = tasks_collection.delete_one({
            "_id": oid,
            "user_id": str(current_user_id()),
        })

        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Task not found"}), 404

        # Rebuild the user's Redis task array after deletion. If it was the last
        # task, Redis will hold an empty JSON array: [].
        redis_synced = sync_user_tasks_to_redis(current_user_id())
        return jsonify({
            "success": True,
            "message": (
                "Task deleted from MongoDB and Redis"
                if redis_synced
                else "Task deleted from MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not delete task")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/redis-tasks", methods=["GET"])
def get_redis_tasks():
    """Authenticated endpoint to inspect the current user's Redis task mirror."""
    auth = login_required()
    if auth:
        return auth

    if redis_client is None:
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Redis is not configured",
        }), 503

    key = redis_tasks_key(current_user_id())
    try:
        raw_value = redis_client.get(key)
        if raw_value is None:
            tasks = []
            cache_exists = False
        else:
            if isinstance(raw_value, bytes):
                raw_value = raw_value.decode("utf-8")
            tasks = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
            cache_exists = True

        return jsonify({
            "success": True,
            "redis": True,
            "key": key,
            "cache_exists": cache_exists,
            "tasks": tasks,
        }), 200
    except Exception:
        app.logger.exception("Could not read task mirror from Redis")
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Could not read tasks from Redis; check Render logs",
        }), 500


# ==================================================
# SCHEDULE — MONGODB + REDIS MIRROR
# ==================================================

@app.route("/api/schedule", methods=["POST"])
def add_schedule():
    auth = login_required()
    if auth:
        return auth

    try:
        data = request.get_json(silent=True) or {}
        time = str(data.get("time", "")).strip()
        activity = str(data.get("activity", "")).strip()

        if not time or not activity:
            return jsonify({
                "success": False,
                "message": "Time and activity are required"
            }), 400

        schedule = {
            "user_id": str(current_user_id()),
            "time": time,
            "activity": activity,
            "created_at": utc_now(),
        }
        result = schedule_collection.insert_one(schedule)
        schedule["_id"] = result.inserted_id
        redis_synced = sync_user_schedules_to_redis(current_user_id())

        return jsonify({
            "success": True,
            "message": (
                "Schedule saved to MongoDB and Redis"
                if redis_synced else
                "Schedule saved to MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
            "schedule": schedule_to_api_dict(schedule),
        }), 201

    except Exception as e:
        app.logger.exception("Could not add schedule")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/schedule", methods=["GET"])
def get_schedule():
    auth = login_required()
    if auth:
        return auth

    try:
        documents = list(
            schedule_collection.find({"user_id": str(current_user_id())})
            .sort("created_at", 1)
        )
        result = [schedule_to_api_dict(item) for item in documents]
        # Each user's existing data is mirrored when they sign in/load the page.
        redis_synced = sync_user_schedules_to_redis(current_user_id())

        return jsonify({
            "success": True,
            "schedule": result,
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not load schedule")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/schedule/<schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id):
    auth = login_required()
    if auth:
        return auth

    oid = object_id(schedule_id)
    if oid is None:
        return jsonify({"success": False, "message": "Invalid schedule ID"}), 400

    try:
        result = schedule_collection.delete_one({
            "_id": oid,
            "user_id": str(current_user_id()),
        })
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Schedule not found"}), 404

        redis_synced = sync_user_schedules_to_redis(current_user_id())
        return jsonify({
            "success": True,
            "message": (
                "Schedule deleted from MongoDB and Redis"
                if redis_synced else
                "Schedule deleted from MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not delete schedule")
        return jsonify({"success": False, "message": str(e)}), 500


# ==================================================
# DAILY HABITS — MONGODB + REDIS MIRROR
# ==================================================

@app.route("/api/habits", methods=["POST"])
def save_habits():
    auth = login_required()
    if auth:
        return auth

    try:
        data = request.get_json(silent=True) or {}
        sleep_time = str(data.get("sleep_time", "")).strip()
        wake_time = str(data.get("wake_time", "")).strip()
        screen_time = data.get("screen_time", 0)
        study_time = data.get("study_time", 0)

        if not sleep_time or not wake_time:
            return jsonify({
                "success": False,
                "message": "Sleep and wake-up time are required"
            }), 400

        try:
            screen_time = float(screen_time)
            study_time = float(study_time)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Screen time and study time must be numbers"
            }), 400

        habit = {
            "user_id": str(current_user_id()),
            "sleep_time": sleep_time,
            "wake_time": wake_time,
            "screen_time": screen_time,
            "study_time": study_time,
            "created_at": utc_now(),
        }
        result = habits_collection.insert_one(habit)
        habit["_id"] = result.inserted_id
        redis_synced = sync_user_habits_to_redis(current_user_id())

        return jsonify({
            "success": True,
            "message": (
                "Daily habits saved to MongoDB and Redis"
                if redis_synced else
                "Daily habits saved to MongoDB, but Redis sync failed; check Render logs"
            ),
            "redis_synced": redis_synced,
            "habit": habit_to_redis_dict(habit),
        }), 201

    except Exception as e:
        app.logger.exception("Could not save daily habits")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/habits", methods=["GET"])
def get_habits():
    auth = login_required()
    if auth:
        return auth

    try:
        habit = habits_collection.find_one(
            {"user_id": str(current_user_id())},
            sort=[("created_at", -1)]
        )
        # Mirror the user's complete habit history; API still returns latest habit
        # in the shape the current React frontend expects.
        redis_synced = sync_user_habits_to_redis(current_user_id())

        if not habit:
            return jsonify({
                "success": True,
                "habit": None,
                "redis_synced": redis_synced,
            }), 200

        return jsonify({
            "success": True,
            "habit": {
                "id": str(habit["_id"]),
                "sleep_time": habit.get("sleep_time", ""),
                "wake_time": habit.get("wake_time", ""),
                "screen_time": habit.get("screen_time", 0),
                "study_time": habit.get("study_time", 0),
            },
            "redis_synced": redis_synced,
        }), 200

    except Exception as e:
        app.logger.exception("Could not load daily habits")
        return jsonify({"success": False, "message": str(e)}), 500


# ==================================================
# REDIS DATA INSPECTION — CURRENT USER ONLY
# ==================================================

@app.route("/api/redis-data", methods=["GET"])
def get_redis_data():
    auth = login_required()
    if auth:
        return auth

    if redis_client is None:
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Redis is not configured",
        }), 503

    user_id = str(current_user_id())
    try:
        # Refresh each mirror from MongoDB first so this endpoint also repairs
        # any cache missed during a previous outage.
        sync_status = sync_all_user_data_to_redis(user_id)

        tasks = read_redis_json(redis_tasks_key(user_id), [])
        schedules = read_redis_json(redis_schedules_key(user_id), [])
        habits = read_redis_json(redis_habits_key(user_id), [])

        return jsonify({
            "success": True,
            "redis": True,
            "user_id": user_id,
            "keys": {
                "tasks": redis_tasks_key(user_id),
                "schedules": redis_schedules_key(user_id),
                "habits": redis_habits_key(user_id),
            },
            "redis_synced": all(sync_status.values()),
            "sync_status": sync_status,
            "data": {
                "tasks": tasks,
                "schedules": schedules,
                "habits": habits,
            },
        }), 200

    except Exception:
        app.logger.exception("Could not read current user's Redis data")
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Could not read Redis data; check Render logs",
        }), 500


# ==================================================
# REDIS HEALTH CHECK
# ==================================================

@app.route("/api/redis-health", methods=["GET"])
def redis_health():
    if redis_client is None:
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Redis is not configured"
        }), 503

    try:
        result = redis_client.ping()
        connected = result is True or str(result).upper() == "PONG"

        return jsonify({
            "success": connected,
            "redis": connected,
            "message": (
                "Redis connection is working"
                if connected
                else "Redis ping returned an unexpected response"
            )
        }), (200 if connected else 500)

    except Exception:
        app.logger.exception("Redis connection failed")
        return jsonify({
            "success": False,
            "redis": False,
            "message": "Redis connection failed; check Render environment variables"
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