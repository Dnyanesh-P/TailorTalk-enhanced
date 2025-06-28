# config/settings.py

# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
