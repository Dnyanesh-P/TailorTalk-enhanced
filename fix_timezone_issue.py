"""
Quick fix script for timezone-related calendar issues
"""
import os
import sys
from datetime import datetime
import pytz
from dotenv import load_dotenv

def fix_timezone_issue():
    """Fix common timezone-related issues"""
    print("🔧 TailorTalk Timezone Fix")
    print("=" * 30)
    
    # Load environment
    load_dotenv()
    
    # Check timezone setting
    timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
    print(f"📍 Configured timezone: {timezone_str}")
    
    try:
        # Test timezone
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        print(f"🕐 Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Test datetime creation
        test_date = "2025-07-05"
        test_time = "15:00"
        
        # Parse date and time
        date_obj = datetime.strptime(test_date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(test_time, '%H:%M').time()
        
        # Combine and localize
        naive_datetime = datetime.combine(date_obj, time_obj)
        aware_datetime = tz.localize(naive_datetime)
        
        print(f"✅ Test datetime creation successful:")
        print(f"   Input: {test_date} {test_time}")
        print(f"   Output: {aware_datetime.isoformat()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Timezone error: {e}")
        return False

def update_env_file():
    """Update .env file with correct timezone settings"""
    env_updates = {
        'TIMEZONE': 'Asia/Kolkata',
        'GOOGLE_CREDENTIALS_PATH': 'config/credentials.json',
        'CALENDAR_ID': 'primary'
    }
    
    print("\n📝 Updating .env file...")
    
    # Read existing .env
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
    
    # Update or add settings
    for key, value in env_updates.items():
        if f"{key}=" in env_content:
            # Update existing
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
            env_content = '\n'.join(lines)
        else:
            # Add new
            env_content += f"\n{key}={value}"
    
    # Write updated .env
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file updated")

if __name__ == "__main__":
    print("🚀 Running TailorTalk Timezone Fix...")
    
    # Fix timezone issue
    if fix_timezone_issue():
        print("✅ Timezone configuration is working correctly")
    else:
        print("❌ Timezone issue detected - updating configuration...")
        update_env_file()
        
        # Test again
        if fix_timezone_issue():
            print("✅ Timezone issue fixed!")
        else:
            print("❌ Unable to fix timezone issue automatically")
            print("💡 Please check your timezone configuration manually")
    
    print("\n🎯 Next steps:")
    print("1. Run: python test_calendar_connection.py")
    print("2. Start the server: python main_with_ai.py")
    print("3. Test booking: 'Book appointment on 5th July at 15:00'")
