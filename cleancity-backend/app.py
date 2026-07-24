from flask import Flask, render_template, jsonify, request
from config import Config
from database.database import db, cors
from routes.routes import routes
from models.models import WasteReport
from flask_migrate import Migrate
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend")
    )

    app.config.from_object(Config)

    # Initialize database and CORS
    db.init_app(app)
    cors.init_app(app)

    # Initialize Flask-Migrate
    Migrate(app, db)

    # Logging
    if not app.debug and not app.testing:
        logs_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "cleancity.log"),
            maxBytes=1024 * 1024 * 5,
            backupCount=3
        )

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s "
            "[in %(pathname)s:%(lineno)d]"
        )

        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # Register API routes
    app.register_blueprint(routes)

    # Health check
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok"
        }), 200

    # Home page
    @app.route("/")
    def home():
        return render_template("index.html")

    # 404 Error
    @app.errorhandler(404)
    def not_found(error):
        if (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        ):
            return jsonify({
                "error": "Not found"
            }), 404

        return render_template("index.html"), 404

    # 500 Error
    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception(error)

        if (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        ):
            return jsonify({
                "error": "Server error"
            }), 500

        return render_template("index.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()

    app.run(debug=True)