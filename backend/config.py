import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask App settings
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))

    # Groq Service
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

    # Database Settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mockster.ai')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS Settings
    CORS_ORIGINS = "http://localhost:3000"