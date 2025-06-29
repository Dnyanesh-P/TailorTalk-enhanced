import sys
import os

print("🔍 Python Path Diagnostics")
print("=" * 50)

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Current Working Directory: {os.getcwd()}")

print("\n📁 Python Path (sys.path):")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n🔍 Testing Imports:")

# Test each import individually
imports_to_test = [
    ("os", "Built-in module"),
    ("dotenv", "python-dotenv package"),
    ("fastapi", "FastAPI package"),
    ("langchain", "LangChain package"),
    ("langchain_openai", "LangChain OpenAI package"),
    ("langgraph", "LangGraph package"),
    ("google.auth", "Google Auth package"),
    ("googleapiclient", "Google API Client package"),
    ("streamlit", "Streamlit package"),
    ("pytz", "PyTZ package")
]

for module_name, description in imports_to_test:
    try:
        __import__(module_name)
        print(f"✅ {module_name}: OK ({description})")
    except ImportError as e:
        print(f"❌ {module_name}: FAILED - {e}")

print("\n🔍 Testing Local Module Imports:")

# Test local file imports
local_files = ["google_calendar", "langgraph_agent"]

for module_name in local_files:
    try:
        # Check if file exists first
        file_path = f"{module_name}.py"
        if os.path.exists(file_path):
            print(f"📁 {file_path}: File exists")
            # Try to import
            __import__(module_name)
            print(f"✅ {module_name}: Import successful")
        else:
            print(f"❌ {file_path}: File not found")
    except Exception as e:
        print(f"❌ {module_name}: Import failed - {e}")

print("\n🔍 Environment Variables:")
env_vars = ["OPENAI_API_KEY", "GOOGLE_CREDENTIALS_PATH", "TIMEZONE"]
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Show only first 20 chars for security
        display_value = value[:20] + "..." if len(value) > 20 else value
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: Not set")
