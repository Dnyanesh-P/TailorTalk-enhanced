"""
Force reload environment variables and test
"""

import os
import sys
from dotenv import load_dotenv

def force_reload_environment():
    """Force reload all environment variables"""
    print("🔄 Force Reloading Environment Variables...")
    
    # Clear existing environment variables related to OpenAI
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
        print("🗑️ Cleared existing OPENAI_API_KEY from environment")
    
    # Force reload .env file
    load_dotenv(override=True)
    print("✅ Reloaded .env file with override=True")
    
    # Check what we got
    new_key = os.getenv('OPENAI_API_KEY')
    if new_key:
        print(f"🔑 New API key loaded: {new_key[:10]}...{new_key[-4:]}")
        return new_key
    else:
        print("❌ Still no API key found")
        return None

def test_with_new_key():
    """Test the newly loaded key"""
    api_key = force_reload_environment()
    
    if not api_key:
        print("❌ Cannot test - no API key available")
        return
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        print("🧪 Testing with OpenAI client...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API test successful!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")

if __name__ == "__main__":
    test_with_new_key()
