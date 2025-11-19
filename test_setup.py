# Test all imports work
print("Testing imports...")

try:
    import fastapi
    print("✅ FastAPI")
except ImportError as e:
    print(f"❌ FastAPI: {e}")

try:
    import openai
    print("✅ OpenAI")
except ImportError as e:
    print(f"❌ OpenAI: {e}")

try:
    import chromadb
    print("✅ ChromaDB")
except ImportError as e:
    print(f"❌ ChromaDB: {e}")

try:
    import PyPDF2
    print("✅ PyPDF2")
except ImportError as e:
    print(f"❌ PyPDF2: {e}")

# Test environment variables
print("\nTesting environment variables...")
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key.startswith("sk-"):
    print(f"✅ OpenAI API Key loaded (starts with: {api_key[:10]}...)")
else:
    print("❌ OpenAI API Key not found or invalid!")


print("🎉 Setup Complete! Ready to code!")