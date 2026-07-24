from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database.database import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citizen")

    complaints = db.relationship("Complaint", backref="reporter", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_municipality(self):
        return self.role == "municipality"


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(256), nullable=True)
    location = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    assigned_to = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reported_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    VALID_STATUSES = ("Pending", "Assigned", "Resolved")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image": self.image,
            "location": self.location,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "reported_by": self.reported_by,
        }
