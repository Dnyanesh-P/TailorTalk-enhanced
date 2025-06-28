"""
Alternative way to run the TailorTalk server
This eliminates any import string issues
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("🚀 Starting TailorTalk AI Booking Agent API...")
    print(f"📁 Credentials path: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set')}")
    print(f"🔑 OpenAI API key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"🌍 Timezone: {os.getenv('TIMEZONE', 'Asia/Kolkata')}")
    print("🌐 API will be available at: http://127.0.0.1:8001")
    print("📚 API docs will be available at: http://127.0.0.1:8001/docs")
    print("🤖 Full AI agent and Google Calendar integration enabled!")
    
    uvicorn.run(
        "main_with_ai:app",  # Updated to match your filename
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
