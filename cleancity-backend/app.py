from flask import Flask, render_template
from config import Config
from database.database import db, cors
from routes.routes import routes
from models.models import WasteReport
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend")
    )

    app.config.from_object(Config)

    db.init_app(app)
    cors.init_app(app)

    app.register_blueprint(routes)

    @app.route("/")
    def home():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()

    app.run(debug=True)