"""
TailorTalk Setup Verification Script
This script checks your current setup and guides you through any remaining issues
"""

import os
import json
import sys
from pathlib import Path

def check_project_structure():
    """Verify the project structure is correct"""
    print("🔍 Checking TailorTalk Project Structure...")
    print("=" * 50)
    
    # Expected structure
    expected_files = {
        'main_with_ai.py': 'Main FastAPI application',
        'config/credentials.json': 'Google OAuth credentials',
        'backend/__init__.py': 'Backend package marker',
        'backend/google_calendar.py': 'Google Calendar integration',
        'backend/langgraph_agent.py': 'AI agent logic',
        'frontend/__init__.py': 'Frontend package marker',
        'frontend/streamlit_app.py': 'Streamlit frontend',
        '.env': 'Environment variables',
        'requirements.txt': 'Python dependencies'
    }
    
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    missing_files = []
    found_files = []
    
    for file_path, description in expected_files.items():
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path} - {description}")
            found_files.append(file_path)
        else:
            print(f"❌ {file_path} - {description} (MISSING)")
            missing_files.append(file_path)
    
    return missing_files, found_files

def check_credentials_file():
    """Check the credentials.json file"""
    print("\n🔐 Checking Google Credentials...")
    print("=" * 40)
    
    credentials_path = Path('config/credentials.json')
    
    if not credentials_path.exists():
        print("❌ credentials.json not found in config/ folder")
        return False
    
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        if 'installed' in creds_data:
            client_info = creds_data['installed']
            print("✅ Valid Desktop Application credentials found")
            print(f"📧 Client ID: {client_info.get('client_id', 'Not found')[:30]}...")
            print(f"🏢 Project ID: {client_info.get('project_id', 'Not found')}")
            print(f"🔗 Auth URI: {client_info.get('auth_uri', 'Not found')}")
            print(f"🎫 Token URI: {client_info.get('token_uri', 'Not found')}")
            
            # Check redirect URIs
            redirect_uris = client_info.get('redirect_uris', [])
            print(f"🔄 Redirect URIs: {redirect_uris}")
            
            return True
        else:
            print("❌ Invalid credentials format")
            print("💡 Make sure you downloaded 'Desktop Application' credentials")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def check_env_file():
    """Check the .env file configuration"""
    print("\n🌍 Checking Environment Configuration...")
    print("=" * 40)
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        create_env_file()
        return False
    
    try:
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        required_vars = {
            'OPENAI_API_KEY': 'OpenAI API key for AI agent',
            'GOOGLE_CREDENTIALS_PATH': 'Path to Google credentials file',
            'CALENDAR_ID': 'Google Calendar ID (usually "primary")',
            'TIMEZONE': 'Your timezone (e.g., Asia/Kolkata)'
        }
        
        missing_vars = []
        
        for var, description in required_vars.items():
            if var in env_content and f'{var}=' in env_content:
                # Check if it has a value
                for line in env_content.split('\n'):
                    if line.startswith(f'{var}='):
                        value = line.split('=', 1)[1].strip()
                        if value and value != 'your_key_here':
                            print(f"✅ {var} - {description}")
                        else:
                            print(f"⚠️ {var} - {description} (SET BUT EMPTY)")
                            missing_vars.append(var)
                        break
            else:
                print(f"❌ {var} - {description} (MISSING)")
                missing_vars.append(var)
        
        return len(missing_vars) == 0
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def create_env_file():
    """Create a template .env file"""
    print("\n📝 Creating .env template...")
    
    env_template = """# TailorTalk Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CREDENTIALS_PATH=config/credentials.json
CALENDAR_ID=primary
TIMEZONE=Asia/Kolkata
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ .env template created")
        print("📝 Please edit .env file and add your actual API keys")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def test_google_auth():
    """Test Google authentication"""
    print("\n🔐 Testing Google Authentication...")
    print("=" * 40)
    
    try:
        # Import after checking files exist
        from backend.google_calendar import get_calendar_manager
        
        print("🔄 Attempting to initialize Google Calendar Manager...")
        calendar_manager = get_calendar_manager()
        
        if calendar_manager and calendar_manager.service:
            print("✅ Google Calendar authentication successful!")
            
            # Test calendar access
            try:
                calendar_list = calendar_manager.service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                print(f"📅 Found {len(calendars)} calendars:")
                for cal in calendars[:3]:  # Show first 3
                    print(f"   • {cal.get('summary', 'Unnamed Calendar')}")
                return True
            except Exception as e:
                print(f"⚠️ Calendar access test failed: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required packages are installed")
        return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure you're added as a test user in Google Cloud Console")
        print("2. Check OAuth consent screen configuration")
        print("3. Try deleting config/token.pickle if it exists")
        return False

def provide_next_steps(missing_files, creds_ok, env_ok, auth_ok):
    """Provide next steps based on verification results"""
    print("\n🎯 NEXT STEPS:")
    print("=" * 20)
    
    if missing_files:
        print("1. 📁 Fix missing files:")
        for file in missing_files:
            print(f"   • Create {file}")
    
    if not creds_ok:
        print("2. 🔐 Fix Google credentials:")
        print("   • Download 'Desktop Application' credentials from Google Cloud Console")
        print("   • Save as config/credentials.json")
    
    if not env_ok:
        print("3. 🌍 Fix environment variables:")
        print("   • Edit .env file with your actual API keys")
        print("   • Make sure GOOGLE_CREDENTIALS_PATH=config/credentials.json")
    
    if not auth_ok:
        print("4. 🔧 Fix Google OAuth:")
        print("   • Add yourself as test user in Google Cloud Console")
        print("   • Go to APIs & Services > OAuth consent screen")
        print("   • Add dnyaneshpurohit@gmail.com to test users")
    
    if creds_ok and env_ok and not auth_ok:
        print("\n🚀 READY TO TEST:")
        print("   Run: python main_with_ai.py")
        print("   Then: streamlit run frontend/streamlit_app.py")

def main():
    """Main verification function"""
    print("🚀 TailorTalk Setup Verification")
    print("=" * 60)
    print("This script will check your TailorTalk setup and guide you through any issues.\n")
    
    # Check project structure
    missing_files, found_files = check_project_structure()
    
    # Check credentials
    creds_ok = check_credentials_file()
    
    # Check environment
    env_ok = check_env_file()
    
    # Test authentication (only if basic setup is complete)
    auth_ok = False
    if not missing_files and creds_ok and env_ok:
        auth_ok = test_google_auth()
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY:")
    print("=" * 30)
    print(f"📁 Project Structure: {'✅ Complete' if not missing_files else '❌ Missing files'}")
    print(f"🔐 Google Credentials: {'✅ Valid' if creds_ok else '❌ Invalid'}")
    print(f"🌍 Environment Config: {'✅ Complete' if env_ok else '❌ Incomplete'}")
    print(f"🔧 Google Authentication: {'✅ Working' if auth_ok else '❌ Not working'}")
    
    # Provide next steps
    provide_next_steps(missing_files, creds_ok, env_ok, auth_ok)
    
    if all([not missing_files, creds_ok, env_ok, auth_ok]):
        print("\n🎉 CONGRATULATIONS!")
        print("Your TailorTalk setup is complete and ready to use!")
        print("\n🚀 To start the application:")
        print("1. Terminal 1: python main.py")
        print("2. Terminal 2: streamlit run frontend/streamlit_app.py")
    else:
        print("\n⚠️ Setup incomplete. Please follow the steps above.")

if __name__ == "__main__":
    main()
