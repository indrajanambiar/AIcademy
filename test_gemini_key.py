
import os
import google.generativeai as genai

os.environ["GOOGLE_API_KEY"] = "AIzaSyC6TjZbUx7D4JVe0b6Gnwe_sN-OCV-uwAQ"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("🔑 Testing Gemini API Key...")
print(f"   Key: {os.environ['GOOGLE_API_KEY'][:20]}...")

try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say 'Hello, I am working!'")
    print(f"\n✅ API Key is valid!")
    print(f"   Response: {response.text}")
except Exception as e:
    print(f"\n❌ API Key test failed!")
    print(f"   Error: {e}")
