import os
import sys
import subprocess
import json
from pathlib import Path
import platform

def check_windows_requirements():
    """Check Windows-specific requirements"""
    print("🔍 Checking Windows requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check if running on Windows
    if platform.system() != "Windows":
        print("⚠️ This script is optimized for Windows")
    
    return True

def create_directory_structure():
    """Create the required directory structure"""
    directories = [
        "backend",
        "frontend", 
        "config",
        "logs",
        "tests",
        "scripts",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_windows_env_file():
    """Create Windows-compatible .env file"""
    env_content = """# TailorTalk Enhanced Configuration (Windows)

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Google Calendar Configuration (Windows paths)
GOOGLE_CREDENTIALS_PATH=config\\credentials.json
CALENDAR_ID=primary
TIMEZONE=Asia/Kolkata

# Application Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
FRONTEND_PORT=8501
DEBUG=True
ENVIRONMENT=development

# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
CORS_ORIGINS=["http://localhost:8501", "http://127.0.0.1:8501"]
ENCRYPTION_ENABLED=True

# Logging Configuration (Windows paths)
LOG_LEVEL=INFO
LOG_FILE=logs\\tailortalk.log
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=300

# Monitoring Configuration
METRICS_ENABLED=True
METRICS_EXPORT_INTERVAL=300
HEALTH_CHECK_INTERVAL=60

# Business Logic Configuration
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=18
DEFAULT_MEETING_DURATION=60
MAX_BOOKING_DAYS_AHEAD=365
MIN_BOOKING_HOURS_AHEAD=1

# Feature Flags
ENHANCED_PARSING_ENABLED=True
SECURE_CREDENTIALS_ENABLED=True
MONITORING_ENABLED=True
AUTO_TIMEZONE_DETECTION=True

# Windows-specific settings
WINDOWS_CONSOLE_ENCODING=utf-8
"""
    
    with open(".env", "w", encoding='utf-8') as f:
        f.write(env_content)
    print("✅ Created Windows-compatible .env file")

def install_dependencies_windows():
    """Install dependencies with Windows-specific handling"""
    print("📦 Installing dependencies for Windows...")
    
    try:
        # Ensure we're using the virtual environment pip
        pip_cmd = [sys.executable, "-m", "pip"]
        
        # Upgrade pip first
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        
        # Install dependencies
        subprocess.run(pip_cmd + ["install", "-r", "requirements_enhanced.txt"], check=True)
        print("✅ Dependencies installed successfully")
        
        # Install Windows-specific packages if needed
        try:
            subprocess.run(pip_cmd + ["install", "pywin32"], check=False)
            print("✅ Windows-specific packages installed")
        except:
            print("⚠️ Some Windows-specific packages may not be available")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running as administrator or check your internet connection")

def create_windows_test_script():
    """Create Windows-compatible test script"""
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Windows-compatible test script for TailorTalk Enhanced
\"\"\"
import asyncio
import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Ensure UTF-8 encoding on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

async def test_api_endpoints():
    \"\"\"Test all API endpoints\"\"\"
    base_url = "http://127.0.0.1:8001"
    
    tests = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/parse-datetime?text=tomorrow at 3 PM", "DateTime parsing"),
        ("POST", "/chat", "Chat endpoint", {"message": "Hello", "user_id": "test_user"}),
    ]
    
    print("🧪 Testing API endpoints...")
    
    for method, endpoint, description, *data in tests:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", json=data[0] if data else {}, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: {str(e)}")

def test_datetime_parsing():
    \"\"\"Test datetime parsing functionality\"\"\"
    print("🕐 Testing datetime parsing...")
    
    test_cases = [
        "tomorrow at 3 PM",
        "next Monday morning",
        "July 15th at 2:30",
        "in 2 weeks at noon",
        "5th August 15:00",
        "4th August 3:30pm"
    ]
    
    try:
        # Add current directory to path for imports
        sys.path.insert(0, os.getcwd())
        from backend.date_time_parser import DateTimeParser
        parser = DateTimeParser()
        
        for test_case in test_cases:
            result = parser.parse_datetime(test_case)
            print(f"  '{test_case}' -> Date: {result.get('date')}, Time: {result.get('time')}")
            
    except ImportError:
        print("❌ Enhanced datetime parser not available")
    except Exception as e:
        print(f"❌ Error testing datetime parser: {e}")

def test_windows_specific():
    \"\"\"Test Windows-specific functionality\"\"\"
    print("🪟 Testing Windows-specific features...")
    
    # Test file paths
    config_path = "config\\\\credentials.json"
    print(f"  Config path format: {config_path}")
    
    # Test encoding
    try:
        test_string = "Testing UTF-8: 🚀 📅 ✅"
        print(f"  UTF-8 encoding: {test_string}")
    except Exception as e:
        print(f"  ❌ Encoding issue: {e}")

if __name__ == "__main__":
    print("🚀 TailorTalk Enhanced Test Suite (Windows)")
    print("=" * 50)
    
    test_windows_specific()
    print()
    test_datetime_parsing()
    print()
    
    # Test API endpoints
    try:
        asyncio.run(test_api_endpoints())
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Make sure the server is running: python main_with_ai.py")
    
    print("\\n✅ Test suite completed!")
    input("Press Enter to exit...")
"""
    
    with open("test_enhanced_windows.py", "w", encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created Windows test script: test_enhanced_windows.py")
