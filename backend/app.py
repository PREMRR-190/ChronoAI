from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# ==================================================
# FLASK
# ==================================================

app = Flask(__name__)
CORS(app)

# ==================================================
# MONGODB
# ==================================================

MONGO_URI = "mongodb://127.0.0.1:27017/"

client = MongoClient(MONGO_URI)

db = client["ChronoAI"]

tasks_collection = db["tasks"]
schedule_collection = db["schedules"]
habits_collection = db["daily_habits"]


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "ChronoAI Backend is running!"
    })


# ==================================================
# TASKS
# ==================================================

@app.route("/api/tasks", methods=["POST"])
def add_task():

    try:

        data = request.get_json()

        title = data.get("title")
        priority = data.get("priority", "Medium")
        hours = data.get("hours", 1)

        if not title:

            return jsonify({
                "success": False,
                "message": "Task title is required"
            }), 400

        task = {

            "title": title,
            "priority": priority,
            "hours": float(hours),
            "completed": False,
            "created_at": datetime.now()

        }

        result = tasks_collection.insert_one(task)

        return jsonify({

            "success": True,

            "task": {

                "id": str(result.inserted_id),
                "title": title,
                "priority": priority,
                "hours": float(hours),
                "completed": False

            }

        }), 201

    except Exception as e:

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    try:

        tasks = list(
            tasks_collection.find().sort(
                "created_at",
                -1
            )
        )

        result = []

        for task in tasks:

            result.append({

                "id": str(task["_id"]),
                "title": task.get("title", ""),
                "priority": task.get(
                    "priority",
                    "Medium"
                ),
                "hours": task.get(
                    "hours",
                    1
                ),
                "completed": task.get(
                    "completed",
                    False
                )

            })

        return jsonify({

            "success": True,
            "tasks": result

        })

    except Exception as e:

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


@app.route(
    "/api/tasks/<task_id>",
    methods=["PUT"]
)
def update_task(task_id):

    try:

        data = request.get_json()

        completed = data.get(
            "completed",
            False
        )

        result = tasks_collection.update_one(

            {
                "_id":
                ObjectId(task_id)
            },

            {
                "$set": {
                    "completed":
                    bool(completed)
                }
            }

        )

        if result.matched_count == 0:

            return jsonify({

                "success": False,
                "message": "Task not found"

            }), 404

        return jsonify({

            "success": True,
            "message":
            "Task updated successfully"

        })

    except Exception as e:

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


@app.route(
    "/api/tasks/<task_id>",
    methods=["DELETE"]
)
def delete_task(task_id):

    try:

        result = tasks_collection.delete_one({

            "_id":
            ObjectId(task_id)

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

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


# ==================================================
# TODAY'S SCHEDULE
# ==================================================

@app.route(
    "/api/schedule",
    methods=["POST"]
)
def add_schedule():

    try:

        data = request.get_json()

        time = data.get("time")
        activity = data.get("activity")

        if not time or not activity:

            return jsonify({

                "success": False,
                "message":
                "Time and activity are required"

            }), 400

        schedule = {

            "time": time,
            "activity": activity,
            "created_at": datetime.now()

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
            "message": str(e)

        }), 500


@app.route(
    "/api/schedule",
    methods=["GET"]
)
def get_schedule():

    try:

        schedules = list(
            schedule_collection.find()
        )

        result = []

        for item in schedules:

            result.append({

                "id":
                str(item["_id"]),

                "time":
                item.get("time", ""),

                "activity":
                item.get(
                    "activity",
                    ""
                )

            })

        return jsonify({

            "success": True,
            "schedule": result

        })

    except Exception as e:

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


@app.route(
    "/api/schedule/<schedule_id>",
    methods=["DELETE"]
)
def delete_schedule(schedule_id):

    try:

        result = schedule_collection.delete_one({

            "_id":
            ObjectId(schedule_id)

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

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


# ==================================================
# DAILY HABITS
# ==================================================

@app.route(
    "/api/habits",
    methods=["POST"]
)
def save_habits():

    try:

        data = request.get_json()

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

            "sleep_time":
            sleep_time,

            "wake_time":
            wake_time,

            "screen_time":
            float(screen_time),

            "study_time":
            float(study_time),

            "created_at":
            datetime.now()

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

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


@app.route(
    "/api/habits",
    methods=["GET"]
)
def get_habits():

    try:

        habit = habits_collection.find_one(
            {},
            sort=[
                ("created_at", -1)
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

        return jsonify({

            "success": False,
            "message": str(e)

        }), 500


# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":

    print()
    print("====================================")
    print("       ChronoAI Backend Server")
    print("====================================")
    print("Database   : ChronoAI")
    print("Collections:")
    print("  - tasks")
    print("  - schedules")
    print("  - daily_habits")
    print("Server     : http://127.0.0.1:5000")
    print("====================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )