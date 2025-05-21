from flask import Flask

from config import Config
from extensions import db, cors
# Import models to ensure they are known to SQLAlchemy, especially for db.create_all()
from models import User, UserProfile, UserAuthLog 

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.interview_routes import interview_bp
from routes.main_routes import main_bp
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    # Note: GroqService is initialized within interview_routes.py using Config

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(main_bp)

    # Create database tables if they don't exist
    # This requires the app context
    with app.app_context():
        db.create_all() 
        # You might want to move db.create_all() to a separate CLI command 
        # for better control in production environments (e.g., using Flask-Migrate).

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=os.environ.get("PORT", 5000)) # Use environment variable for port if available