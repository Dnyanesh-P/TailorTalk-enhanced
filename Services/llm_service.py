import openai
from config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

class LLMService:
    async def extract_intent(self, message: str, conversation_history: list) -> dict:
        # Replace with OpenAI or other model logic
        return {"intent": "BOOKING_REQUEST", "confidence": 0.93}

    async def parse_datetime(self, message: str, user_timezone: str) -> dict:
        # Replace with real model/dateparser logic
        from datetime import datetime, timedelta
        return {"datetime": datetime.now() + timedelta(days=1), "duration": 60}

    async def generate_response(self, intent, message, available_slots, booking_confirmed, conversation_history):
        return f"I found {len(available_slots)} available slots. Shall I book one for you?"