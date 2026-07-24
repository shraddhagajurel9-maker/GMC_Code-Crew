import os
from flask import Flask, render_template, jsonify, request
from config import Config
from database.database import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Create upload folder if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # Register blueprints
    from routes.routes import main
    app.register_blueprint(main)

    # Create tables and seed data inside app context
    with app.app_context():
        from models.models import User, Complaint  # noqa: F401
        db.create_all()
        _seed_defaults()

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("404.html"), 500

    return app


def _seed_defaults():
    """Create default users if the database is empty."""
    from models.models import User

    if User.query.first() is None:
        admin = User(username="admin", email="admin@municipality.com", role="municipality")
        admin.set_password("admin123")

        citizen = User(username="citizen", email="citizen@clean.com", role="citizen")
        citizen.set_password("citizen123")

        db.session.add_all([admin, citizen])
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
