from flask import Flask, jsonify
from config import Config
from extensions import db, cors
from models.user import User
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    cors.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    @app.route('/')
    def health_check():
        return jsonify({
            "status": "ok",
            "message": "SkillBridge backend is running"
        })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
