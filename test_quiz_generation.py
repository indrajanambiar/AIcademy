
import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "backend"))

# Set env for this test
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["LLM_MODEL"] = "gemini-2.5-flash"
os.environ["GOOGLE_API_KEY"] = "AIzaSyC6TjZbUx7D4JVe0b6Gnwe_sN-OCV-uwAQ"
os.environ["SECRET_KEY"] = "test"

from app.services.adaptive_assessment_service import adaptive_assessment_service

async def test_quiz():
    print("=" * 80)
    print("🧪 TESTING QUIZ GENERATION")
    print("=" * 80)
    
    try:
        print("\n📝 Generating quiz for Python...")
        quiz = await adaptive_assessment_service.generate_diagnostic_quiz(
            subject="Python"
        )
        
        print("\n✅ Quiz generated!")
        print(f"   Questions count: {len(quiz.get('questions', []))}")
        print(f"   Title: {quiz.get('title')}")
        print(f"   Used RAG: {quiz.get('metadata', {}).get('used_rag')}")
        
        print("\n📋 Questions:")
        for i, q in enumerate(quiz.get("questions", []), 1):
            print(f"\n   Question {i} ({q.get('difficulty', 'N/A')}):")
            print(f"   Q: {q.get('question', 'N/A')[:100]}...")
            print(f"   Options: {list(q.get('options', {}).keys())}")
            print(f"   Correct: {q.get('correct_answer', 'N/A')}")
        
        if len(quiz.get("questions", [])) == 0:
            print("\n❌ NO QUESTIONS FOUND!")
            print("   Full quiz response:")
            print(quiz)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_quiz())
