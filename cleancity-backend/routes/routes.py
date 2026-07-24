from flask import Blueprint, jsonify, request

from database.database import db
from models.models import WasteReport, User, VALID_ROLES


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


# ---------------------------------------------------------------------------
# WasteReport CRUD endpoints
# ---------------------------------------------------------------------------

ALLOWED_STATUSES = {"pending", "in_progress", "resolved"}


@routes.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    location = data.get("location")
    description = data.get("description")

    if not location or not str(location).strip():
        return jsonify({"error": "'location' is required"}), 400

    if not description or not str(description).strip():
        return jsonify({"error": "'description' is required"}), 400

    status = data.get("status", "pending")
    if status not in ALLOWED_STATUSES:
        return jsonify({
            "error": "'status' must be one of "
            + ", ".join(sorted(ALLOWED_STATUSES))
        }), 400

    report = WasteReport(
        location=str(location).strip(),
        description=str(description).strip(),
        status=status
    )

    db.session.add(report)
    db.session.commit()

    return jsonify(report.to_dict()), 201


@routes.route("/api/reports", methods=["GET"])
def list_reports():
    reports = WasteReport.query.order_by(WasteReport.id).all()
    return jsonify([report.to_dict() for report in reports]), 200


@routes.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    report = db.session.get(WasteReport, report_id)

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    return jsonify(report.to_dict()), 200


@routes.route("/api/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    report = db.session.get(WasteReport, report_id)

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if "location" in data:
        location = data.get("location")
        if not location or not str(location).strip():
            return jsonify({"error": "'location' cannot be empty"}), 400
        report.location = str(location).strip()

    if "description" in data:
        description = data.get("description")
        if not description or not str(description).strip():
            return jsonify({"error": "'description' cannot be empty"}), 400
        report.description = str(description).strip()

    if "status" in data:
        status = data.get("status")
        if status not in ALLOWED_STATUSES:
            return jsonify({
                "error": "'status' must be one of "
                + ", ".join(sorted(ALLOWED_STATUSES))
            }), 400
        report.status = status

    db.session.commit()

    return jsonify(report.to_dict()), 200


@routes.route("/api/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    report = db.session.get(WasteReport, report_id)

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    db.session.delete(report)
    db.session.commit()

    return jsonify({"message": "Report deleted", "id": report_id}), 200


# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------


@routes.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name or not str(name).strip():
        return jsonify({"error": "'name' is required"}), 400

    if not email or not str(email).strip():
        return jsonify({"error": "'email' is required"}), 400

    if not password or not str(password).strip():
        return jsonify({"error": "'password' is required"}), 400

    if role not in VALID_ROLES:
        return jsonify({
            "error": "'role' must be one of " + ", ".join(sorted(VALID_ROLES))
        }), 400

    email = str(email).strip().lower()

    existing = User.query.filter_by(email=email).first()
    if existing is not None:
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=str(name).strip(),
        email=email,
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict()
    }), 201


@routes.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "'email' and 'password' are required"}), 400

    email = str(email).strip().lower()

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200