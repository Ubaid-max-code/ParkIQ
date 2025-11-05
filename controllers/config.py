# config.py

import os
from dotenv import load_dotenv

load_dotenv()  #Load variables from .env file

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/parking.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
