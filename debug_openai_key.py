"""
Debug script to check OpenAI API key configuration and test it
"""

import os
from dotenv import load_dotenv
import requests

def check_openai_configuration():
    """Check OpenAI API key configuration and test it"""
    print("🔍 Debugging OpenAI API Key Configuration")
    print("=" * 60)
    
    # Force reload environment variables
    load_dotenv(override=True)
    
    # Check if .env file exists
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        print(f"✅ .env file found at: {os.path.abspath(env_file_path)}")
        
        # Read .env file content
        with open(env_file_path, 'r') as f:
            env_content = f.read()
        
        print("\n📄 .env file content:")
        for line in env_content.split('\n'):
            if line.strip() and not line.startswith('#'):
                if 'OPENAI_API_KEY' in line:
                    key_part = line.split('=')[1] if '=' in line else ''
                    masked_key = key_part[:10] + "..." + key_part[-4:] if len(key_part) > 14 else key_part
                    print(f"   {line.split('=')[0]}={masked_key}")
                else:
                    print(f"   {line}")
    else:
        print(f"❌ .env file not found at: {os.path.abspath(env_file_path)}")
        return False
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"\n🔑 OpenAI API Key Status:")
    if not api_key:
        print("❌ No API key found in environment")
        return False
    elif api_key == "your_openai_api_key_here":
        print("❌ API key is still the placeholder value")
        return False
    else:
        print(f"✅ API key loaded: {api_key[:10]}...{api_key[-4:]}")
        print(f"📏 Key length: {len(api_key)} characters")
        
        # Check if it starts with the correct prefix
        if api_key.startswith('sk-'):
            print("✅ Key format looks correct (starts with 'sk-')")
        else:
            print("⚠️ Key format might be incorrect (should start with 'sk-')")
    
    # Test the API key
    print(f"\n🧪 Testing OpenAI API Key...")
    try:
        # Test with requests first (simpler)
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        test_payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'max_tokens': 5
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OpenAI API key is working correctly!")
            data = response.json()
            print(f"🤖 Test response: {data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid or unauthorized")
            print(f"Error: {response.text}")
            return False
        elif response.status_code == 429:
            print("❌ Rate limit or quota exceeded")
            print(f"Error: {response.text}")
            
            # Parse the error for more details
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"Detailed error: {error_message}")
            except:
                pass
            return False
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def check_openai_account_status():
    """Check OpenAI account status and usage"""
    print(f"\n💳 Checking OpenAI Account Status...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key available for account check")
        return
    
    try:
        # Check account usage (this endpoint might require different permissions)
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Try to get models list (this is usually allowed)
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model['id'] for model in models_data.get('data', [])]
            gpt_models = [m for m in available_models if 'gpt' in m.lower()]
            print(f"✅ Account has access to {len(gpt_models)} GPT models")
            print(f"Available GPT models: {', '.join(gpt_models[:5])}")
        else:
            print(f"⚠️ Could not check models: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Could not check account status: {e}")

def fix_suggestions():
    """Provide suggestions to fix the issue"""
    print(f"\n🔧 TROUBLESHOOTING SUGGESTIONS:")
    print("=" * 40)
    
    print("1. 🔄 **Restart your application completely**")
    print("   • Stop the FastAPI server (Ctrl+C)")
    print("   • Restart: python main_with_ai.py")
    
    print("\n2. 📝 **Verify your .env file**")
    print("   • Make sure there are no extra spaces")
    print("   • Format: OPENAI_API_KEY=sk-your-actual-key-here")
    print("   • No quotes around the key")
    
    print("\n3. 🔑 **Check your OpenAI account**")
    print("   • Go to: https://platform.openai.com/api-keys")
    print("   • Verify the key is active")
    print("   • Check usage limits: https://platform.openai.com/usage")
    
    print("\n4. 💰 **Check billing**")
    print("   • Go to: https://platform.openai.com/account/billing")
    print("   • Make sure you have credits or a payment method")
    
    print("\n5. 🆕 **Try creating a new API key**")
    print("   • Sometimes keys can have issues")
    print("   • Delete the old one and create a fresh one")

if __name__ == "__main__":
    success = check_openai_configuration()
    check_openai_account_status()
    
    if not success:
        fix_suggestions()
    
    print(f"\n🎯 SUMMARY:")
    if success:
        print("✅ Your OpenAI API key is working correctly!")
        print("The issue might be in how the application is loading the key.")
        print("Try restarting your FastAPI server completely.")
    else:
        print("❌ There's an issue with your OpenAI API key.")
        print("Follow the troubleshooting suggestions above.")
