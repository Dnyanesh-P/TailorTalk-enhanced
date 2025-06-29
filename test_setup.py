#!/usr/bin/env python3
"""
Quick test script to verify your AI booking agent setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment variables and file paths"""
    print("🔍 Testing Environment Setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API Key: Found (starts with {openai_key[:20]}...)")
    else:
        print("❌ OpenAI API Key: Not found")
        return False
    
    # Check Google credentials path
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
    if creds_path and os.path.exists(creds_path):
        print(f"✅ Google Credentials: Found at {creds_path}")
    else:
        print(f"❌ Google Credentials: Not found at {creds_path}")
        return False
    
    # Check timezone
    timezone = os.getenv('TIMEZONE', 'Asia/Kolkata')
    print(f"✅ Timezone: {timezone}")
    
    return True

def test_imports():
    """Test if all required packages can be imported"""
    print("\n🔍 Testing Package Imports...")
    
    packages = [
        'fastapi',
        'uvicorn', 
        'streamlit',
        'langgraph',
        'langchain',
        'langchain_openai',
        'google.auth',
        'googleapiclient',
        'openai',
        'pytz'
    ]
    
    failed_imports = []
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}: OK")
        except ImportError as e:
            print(f"❌ {package}: Failed - {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI Connection...")
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Simple test
        from langchain.schema import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'Hello, AI agent is working!'")])
        print(f"✅ OpenAI Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Connection Failed: {e}")
        return False

def test_google_calendar():
    """Test Google Calendar setup"""
    print("\n🔍 Testing Google Calendar Setup...")
    
    try:
        from google_calendar import get_calendar_manager
        
        calendar_manager = get_calendar_manager()
        print("✅ Google Calendar Manager: Initialized")
        
        # Test getting availability for today
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        slots = calendar_manager.get_availability(today)
        print(f"✅ Calendar Availability: Found {len(slots)} slots for {today}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Calendar Failed: {e}")
        return False

def test_langgraph_agent():
    """Test LangGraph agent initialization"""
    print("\n🔍 Testing LangGraph Agent...")
    
    try:
        from langgraph_agent import BookingAgent
        
        agent = BookingAgent()
        print("✅ BookingAgent: Initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ BookingAgent Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI Booking Agent Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Package Imports", test_imports),
        ("OpenAI Connection", test_openai_connection),
        ("Google Calendar", test_google_calendar),
        ("LangGraph Agent", test_langgraph_agent)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your AI booking agent is ready to use!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. In another terminal: streamlit run streamlit_app.py")
        print("3. Open http://localhost:8501 and start chatting!")
    else:
        print("🔧 Some tests failed. Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()
