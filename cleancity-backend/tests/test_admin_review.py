import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text
import config
from app import create_app, _ensure_schema
from database.database import db
from models.models import Complaint, User


class AdminReviewTestCase(unittest.TestCase):
    def setUp(self):
        config.Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            admin = User(username="admin", email="admin@example.com", role="municipality")
            admin.set_password("password")
            citizen = User(username="citizen", email="citizen@example.com", role="citizen")
            citizen.set_password("password")
            db.session.add_all([admin, citizen])
            db.session.commit()

            complaint = Complaint(
                title="Broken drain",
                description="Water is overflowing near the road.",
                location="Kathmandu",
                reported_by=citizen.id,
            )
            db.session.add(complaint)
            db.session.commit()
            self.complaint_id = complaint.id

    def test_ensure_schema_adds_missing_columns(self):
        with self.app.app_context():
            db.session.execute(text("DROP TABLE IF EXISTS complaints"))
            db.session.execute(
                text(
                    "CREATE TABLE complaints (id INTEGER PRIMARY KEY, title VARCHAR(200), description TEXT, image VARCHAR(256), location VARCHAR(256), status VARCHAR(20), assigned_to VARCHAR(120), created_at DATETIME, reported_by INTEGER)"
                )
            )
            db.session.commit()

            _ensure_schema()

            inspector = inspect(db.engine)
            columns = {column["name"] for column in inspector.get_columns("complaints")}
            self.assertIn("remarks", columns)
            self.assertIn("updated_at", columns)
            self.assertIn("department", columns)

    def test_admin_can_update_status_and_remarks(self):
        self.client.post(
            "/login",
            data={"username": "admin", "password": "password"},
            follow_redirects=True,
        )

        response = self.client.post(
            f"/update-status/{self.complaint_id}",
            data={
                "status": "Resolved",
                "assigned_to": "Ward Officer",
                "remarks": "Repaired and inspected.",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            complaint = db.session.get(Complaint, self.complaint_id)
            self.assertEqual(complaint.status, "Resolved")
            self.assertEqual(complaint.assigned_to, "Ward Officer")
            self.assertEqual(complaint.remarks, "Repaired and inspected.")
            self.assertIsNotNone(complaint.updated_at)


if __name__ == "__main__":
    unittest.main()
