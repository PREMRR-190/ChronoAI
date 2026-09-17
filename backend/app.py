from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

# Render environment variable
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    os.environ.get(
        "CHRONOAI_SECRET_KEY",
        "dev-secret-change-me"
    )
)

# =========================================================
# PRODUCTION SESSION CONFIGURATION
# =========================================================

PRODUCTION = (
    os.environ.get("PRODUCTION", "false").lower() == "true"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = PRODUCTION

if PRODUCTION:
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
else:
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =========================================================
# CORS
# =========================================================

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "http://localhost:5173"
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_URL,
    "https://chronoai-orcin.vercel.app"
]

# Remove duplicates
allowed_origins = list(set(allowed_origins))


CORS(
    app,
    supports_credentials=True,
    origins=allowed_origins
)


# =========================================================
# MONGODB ATLAS
# =========================================================

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    print("WARNING: MONGO_URI environment variable is not set.")

    # Local development fallback
    MONGO_URI = "mongodb://127.0.0.1:27017/"


try:

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000
    )

    # Test MongoDB connection
    client.admin.command("ping")

    print("MongoDB connection successful")

except Exception as e:

    print("MongoDB connection error:", e)


db = client["ChronoAI"]

users_collection = db["users"]
tasks_collection = db["tasks"]
schedule_collection = db["schedules"]
habits_collection = db["daily_habits"]


# =========================================================
# AUTHENTICATION HELPER
# =========================================================

def get_logged_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    try:

        user = users_collection.find_one({
            "_id": ObjectId(user_id)
        })

        return user

    except Exception as e:

        print("GET LOGGED USER ERROR:", e)

        return None


def require_login():

    user = get_logged_user()

    if not user:
        return None

    return str(user["_id"])


# =========================================================
# HOME / HEALTH CHECK
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "login_system": True,
        "message": "ChronoAI Backend is running!"
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400


        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        if not username:

            return jsonify({
                "success": False,
                "message": "Username is required"
            }), 400


        if not password:

            return jsonify({
                "success": False,
                "message": "Password is required"
            }), 400


        if len(username) < 3:

            return jsonify({
                "success": False,
                "message":
                    "Username must contain at least 3 characters"
            }), 400


        if len(password) < 4:

            return jsonify({
                "success": False,
                "message":
                    "Password must contain at least 4 characters"
            }), 400


        # =================================================
        # CHECK EXISTING USER
        # =================================================

        existing_user = users_collection.find_one({
            "username": username
        })


        if existing_user:

            return jsonify({
                "success": False,
                "message": "Username already exists"
            }), 409


        # =================================================
        # HASH PASSWORD
        # =================================================

        password_hash = generate_password_hash(
            password
        )


        # =================================================
        # CREATE USER
        # =================================================

        new_user = {

            "username": username,

            "password": password_hash,

            "created_at": datetime.utcnow()

        }


        result = users_collection.insert_one(
            new_user
        )


        # =================================================
        # LOGIN USER AUTOMATICALLY
        # =================================================

        session.clear()

        session["user_id"] = str(
            result.inserted_id
        )

        session["username"] = username


        print(
            "REGISTER:",
            username,
            "USER ID:",
            str(result.inserted_id)
        )


        return jsonify({

            "success": True,

            "message":
                "Account created successfully",

            "user": {

                "id":
                    str(result.inserted_id),

                "username":
                    username

            }

        }), 201


    except Exception as e:

        print("REGISTER ERROR:", e)

        return jsonify({

            "success": False,

            "message":
                "Registration failed: " + str(e)

        }), 500


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No login data received"

            }), 400


        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        if not username or not password:

            return jsonify({

                "success": False,

                "message":
                    "Username and password are required"

            }), 400


        # =================================================
        # FIND USER IN MONGODB
        # =================================================

        user = users_collection.find_one({

            "username": username

        })


        if not user:

            print(
                "LOGIN FAILED - USER NOT FOUND:",
                username
            )

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password"

            }), 401


        # =================================================
        # CHECK PASSWORD
        # =================================================

        stored_password = user.get(
            "password",
            ""
        )


        if not check_password_hash(
            stored_password,
            password
        ):

            print(
                "LOGIN FAILED - WRONG PASSWORD:",
                username
            )

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password"

            }), 401


        # =================================================
        # CREATE SESSION
        # =================================================

        session.clear()

        session["user_id"] = str(
            user["_id"]
        )

        session["username"] = user["username"]


        print(
            "LOGIN SUCCESS:",
            user["username"],
            "USER ID:",
            str(user["_id"])
        )


        return jsonify({

            "success": True,

            "message":
                "Login successful",

            "user": {

                "id":
                    str(user["_id"]),

                "username":
                    user["username"]

            }

        })


    except Exception as e:

        print("LOGIN ERROR:", e)

        return jsonify({

            "success": False,

            "message":
                "Login failed: " + str(e)

        }), 500


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/me", methods=["GET"])
def me():

    try:

        user = get_logged_user()


        if not user:

            return jsonify({

                "success": False,

                "logged_in": False

            })


        return jsonify({

            "success": True,

            "logged_in": True,

            "user": {

                "id":
                    str(user["_id"]),

                "username":
                    user["username"]

            }

        })


    except Exception as e:

        print("ME ERROR:", e)

        return jsonify({

            "success": False,

            "logged_in": False

        })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    username = session.get(
        "username",
        "Unknown"
    )

    print(
        "LOGOUT:",
        username
    )

    session.clear()


    return jsonify({

        "success": True,

        "message":
            "Logged out successfully"

    })


# =========================================================
# TEST AUTHENTICATION
# =========================================================

@app.route("/api/test-auth", methods=["GET"])
def test_auth():

    user_id = session.get(
        "user_id"
    )

    username = session.get(
        "username"
    )


    return jsonify({

        "success": True,

        "logged_in":
            bool(user_id),

        "user_id":
            user_id,

        "username":
            username

    })


# =========================================================
# TASKS - ADD
# =========================================================

@app.route("/api/tasks", methods=["POST"])
def add_task():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        data = request.get_json() or {}


        title = str(
            data.get("title", "")
        ).strip()

        priority = data.get(
            "priority",
            "Medium"
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


        task = {

            "user_id":
                user_id,

            "title":
                title,

            "priority":
                priority,

            "hours":
                float(hours),

            "completed":
                False,

            "created_at":
                datetime.utcnow()

        }


        result = tasks_collection.insert_one(
            task
        )


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
                    float(hours),

                "completed":
                    False

            }

        }), 201


    except Exception as e:

        print("ADD TASK ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# TASKS - GET
# =========================================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        tasks = list(

            tasks_collection.find({

                "user_id":
                    user_id

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

        })


    except Exception as e:

        print("GET TASKS ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# TASKS - UPDATE
# =========================================================

@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        data = request.get_json() or {}


        completed = bool(
            data.get(
                "completed",
                False
            )
        )


        result = tasks_collection.update_one(

            {

                "_id":
                    ObjectId(task_id),

                "user_id":
                    user_id

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

        })


    except Exception as e:

        print("UPDATE TASK ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# TASKS - DELETE
# =========================================================

@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        result = tasks_collection.delete_one({

            "_id":
                ObjectId(task_id),

            "user_id":
                user_id

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

        })


    except Exception as e:

        print("DELETE TASK ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# SCHEDULE - ADD
# =========================================================

@app.route("/api/schedule", methods=["POST"])
def add_schedule():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        data = request.get_json() or {}


        time = data.get("time")

        activity = str(
            data.get(
                "activity",
                ""
            )
        ).strip()


        if not time or not activity:

            return jsonify({

                "success": False,

                "message":
                    "Time and activity are required"

            }), 400


        schedule = {

            "user_id":
                user_id,

            "time":
                time,

            "activity":
                activity,

            "created_at":
                datetime.utcnow()

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

        print("ADD SCHEDULE ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# SCHEDULE - GET
# =========================================================

@app.route("/api/schedule", methods=["GET"])
def get_schedule():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        schedules = list(

            schedule_collection.find({

                "user_id":
                    user_id

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

        })


    except Exception as e:

        print("GET SCHEDULE ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# SCHEDULE - DELETE
# =========================================================

@app.route("/api/schedule/<schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id):

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        result = schedule_collection.delete_one({

            "_id":
                ObjectId(schedule_id),

            "user_id":
                user_id

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

        })


    except Exception as e:

        print("DELETE SCHEDULE ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# HABITS - SAVE
# =========================================================

@app.route("/api/habits", methods=["POST"])
def save_habits():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        data = request.get_json() or {}


        sleep_time = data.get(
            "sleep_time"
        )

        wake_time = data.get(
            "wake_time"
        )

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


        habit = {

            "user_id":
                user_id,

            "sleep_time":
                sleep_time,

            "wake_time":
                wake_time,

            "screen_time":
                float(screen_time),

            "study_time":
                float(study_time),

            "created_at":
                datetime.utcnow()

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
                    float(screen_time),

                "study_time":
                    float(study_time)

            }

        }), 201


    except Exception as e:

        print("SAVE HABITS ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# HABITS - GET
# =========================================================

@app.route("/api/habits", methods=["GET"])
def get_habits():

    try:

        user_id = require_login()

        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "Please login first"

            }), 401


        habit = habits_collection.find_one(

            {
                "user_id":
                    user_id
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

            })


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

        })


    except Exception as e:

        print("GET HABITS ERROR:", e)

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("          ChronoAI Backend")
    print("==========================================")
    print("Database : ChronoAI")
    print("USER DATA ISOLATION ENABLED")
    print("==========================================")
    print()


    # IMPORTANT:
    # 0.0.0.0 is required for Render

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=False

    )