from database.database import db


class WasteReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default="pending")

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "description": self.description,
            "status": self.status
        }