from flask import Blueprint, jsonify


routes = Blueprint("routes", __name__)


@routes.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "CleanCity Nepal backend is running"
    })


@routes.route("/api/welcome", methods=["GET"])
def welcome():
    return jsonify({
        "status": "success",
        "message": "Welcome to CleanCity Nepal"
    })