from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

auth = Blueprint("auth", __name__)

# MongoDB
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

client = MongoClient(MONGO_URI)
db = client["ChronoAI"]

users_collection = db["users"]


# =========================================================
# REGISTER
# =========================================================

@auth.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # Check empty fields
    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    # Check password length
    if len(password) < 4:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 4 characters"
        }), 400

    # Check passwords
    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match"
        }), 400

    # Check existing user
    existing_user = users_collection.find_one({
        "username": username
    })

    if existing_user:
        return jsonify({
            "success": False,
            "message": "Username already exists"
        }), 409

    # Hash password
    password_hash = generate_password_hash(password)

    # Create user
    user = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }

    result = users_collection.insert_one(user)

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "user_id": str(result.inserted_id)
    }), 201


# =========================================================
# LOGIN
# =========================================================

@auth.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    # Find user
    user = users_collection.find_one({
        "username": username
    })

    # Invalid username
    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    # Invalid password
    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    # Store login session
    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user_id": str(user["_id"]),
        "username": user["username"]
    })


# =========================================================
# CHECK CURRENT LOGIN
# =========================================================

@auth.route("/api/me", methods=["GET"])
def current_user():

    if "user_id" not in session:
        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "user_id": session["user_id"],
        "username": session["username"]
    })


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })