
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock settings if needed, but let's try to rely on env or defaults
os.environ["SECRET_KEY"] = "debug_secret" 

from app.services.adaptive_assessment_service import adaptive_assessment_service

async def test_service():
    print("🚀 Testing AdaptiveAssessmentService...")
    
    try:
        quiz = await adaptive_assessment_service.generate_diagnostic_quiz(
            subject="Python"
        )
        print("✅ Quiz generated successfully!")
        print(f"   Questions: {len(quiz.get('questions', []))}")
        print(f"   Used RAG: {quiz.get('metadata', {}).get('used_rag')}")
        
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service())
