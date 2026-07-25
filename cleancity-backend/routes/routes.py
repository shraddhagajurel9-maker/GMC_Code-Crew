import os
import uuid
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from database.database import db
from models.models import User, Complaint, Department

main = Blueprint("main", __name__)


def municipality_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "municipality":
            flash("Municipality access only.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# ---- Public ----

@main.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status="Pending").count()
    resolved = Complaint.query.filter_by(status="Resolved").count()
    return render_template(
        "landing.html",
        total=total, pending=pending, resolved=resolved
    )


# ---- Auth ----

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "citizen")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        if role not in ("citizen", "municipality"):
            role = "citizen"

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created! Welcome.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.landing"))


# ---- Citizen Dashboard ----

@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "municipality":
        return redirect(url_for("main.admin_dashboard"))

    my_complaints = (
        Complaint.query
        .filter_by(reported_by=current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    total = len(my_complaints)
    pending = sum(1 for c in my_complaints if c.status == "Pending")
    assigned = sum(1 for c in my_complaints if c.status == "Assigned")
    resolved = sum(1 for c in my_complaints if c.status == "Resolved")

    return render_template(
        "dashboard.html",
        complaints=my_complaints,
        total=total, pending=pending,
        assigned=assigned, resolved=resolved
    )


# ---- Report Complaint ----

@main.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        image_file = request.files.get("image")

        if not title or not description or not location:
            flash("Title, description, and location are required.", "danger")
            return render_template("report.html")

        filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                ext = image_file.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                image_file.save(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                )
            else:
                flash("Only PNG, JPG, JPEG, GIF files allowed.", "warning")
                return render_template("report.html")

        complaint = Complaint(
            title=title,
            description=description,
            location=location,
            image=filename,
            reported_by=current_user.id,
        )
        db.session.add(complaint)
        db.session.commit()

        flash("Complaint submitted successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("report.html")


# ---- Complaint List ----

@main.route("/complaints")
@login_required
def complaints():
    if current_user.role == "municipality":
        all_complaints = (
            Complaint.query
            .order_by(Complaint.created_at.desc())
            .all()
        )
    else:
        all_complaints = (
            Complaint.query
            .filter_by(reported_by=current_user.id)
            .order_by(Complaint.created_at.desc())
            .all()
        )
    return render_template("complaints.html", complaints=all_complaints)


# ---- Complaint Detail ----

@main.route("/complaint/<int:complaint_id>")
@login_required
def complaint_detail(complaint_id):
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        flash("Complaint not found.", "danger")
        return redirect(url_for("main.complaints"))

    if (
        current_user.role != "municipality"
        and complaint.reported_by != current_user.id
    ):
        flash("Access denied.", "danger")
        return redirect(url_for("main.complaints"))

    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template("complaint_detail.html", complaint=complaint, departments=departments)


# ---- Update Status (Municipality) ----

@main.route("/update-status/<int:complaint_id>", methods=["POST"])
@municipality_required
def update_status(complaint_id):
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        flash("Complaint not found.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    new_status = request.form.get("status", "")
    assign_to = request.form.get("assigned_to", "").strip()
    department = request.form.get("department", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if new_status in Complaint.VALID_STATUSES:
        complaint.status = new_status

    complaint.assigned_to = assign_to or None
    complaint.department = department or None
    complaint.remarks = remarks or None
    complaint.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    flash(f"Complaint #{complaint.id} updated to {complaint.status}.", "success")
    return redirect(url_for("main.complaint_detail", complaint_id=complaint.id))


# ---- Admin Dashboard ----

@main.route("/admin")
@municipality_required
def admin_dashboard():
    all_complaints = (
        Complaint.query
        .order_by(Complaint.created_at.desc())
        .all()
    )
    total = len(all_complaints)
    pending = sum(1 for c in all_complaints if c.status == "Pending")
    assigned = sum(1 for c in all_complaints if c.status == "Assigned")
    resolved = sum(1 for c in all_complaints if c.status == "Resolved")

    return render_template(
        "admin.html",
        complaints=all_complaints,
        total=total, pending=pending,
        assigned=assigned, resolved=resolved
    )


@main.route("/admin/complaints")
@municipality_required
def admin_complaints():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template("admin_complaints.html", complaints=complaints, departments=departments)


@main.route("/admin/departments", methods=["GET", "POST"])
@municipality_required
def admin_departments():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "danger")
        else:
            existing = Department.query.filter_by(name=name).first()
            if existing:
                flash("Department already exists.", "warning")
            else:
                department = Department(name=name, description=description or None)
                db.session.add(department)
                db.session.commit()
                flash(f"Department '{name}' added.", "success")

    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template("admin_departments.html", departments=departments)


@main.route("/admin/departments/<int:department_id>/delete", methods=["POST"])
@municipality_required
def delete_department(department_id):
    department = db.session.get(Department, department_id)
    if not department:
        flash("Department not found.", "danger")
        return redirect(url_for("main.admin_departments"))

    db.session.delete(department)
    db.session.commit()
    flash("Department removed.", "success")
    return redirect(url_for("main.admin_departments"))
