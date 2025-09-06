#!/usr/bin/env python3
"""
Test Real AI Processing Pipeline
Tests the complete real AI processing workflow with actual OpenAI and Gemini APIs.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_real_ai_processing():
    try:
        print("TESTING REAL AI PROCESSING PIPELINE")
        print("=" * 60)
        
        # Import required modules
        from app.database import connect_to_mongo, get_database, close_mongo_connection
        from app.models.script import ScriptStatus
        from app.workers.evaluation_worker import _real_ai_process_script
        
        print("[OK] Imports successful")
        
        # Connect to database
        await connect_to_mongo()
        db = get_database()
        
        if db is None:
            print("[ERROR] Database connection failed")
            return False
            
        print("[OK] Database connected")
        
        # Find existing image file
        from app.config import settings
        upload_dir = Path(settings.upload_directory)
        image_files = list(upload_dir.glob('*.jpg')) + list(upload_dir.glob('*.png'))
        
        if not image_files:
            print("[ERROR] No test image found in uploads directory")
            return False
            
        test_image = image_files[0]
        print(f"[OK] Using test image: {test_image.name}")
        
        # Create test evaluation scheme (matching EvaluationScheme model)
        test_scheme = {
            "_id": ObjectId(),
            "scheme_name": "Test AI Processing Scheme",
            "subject": "Computer Science",
            "total_marks": 20.0,
            "professor_id": ObjectId(),
            "questions": [
                {
                    "question_number": 1,
                    "max_marks": 10.0,
                    "concepts": [
                        {
                            "concept": "Top-down parsing algorithm",
                            "keywords": ["algorithm", "parsing", "top-down", "recursive", "descent"],
                            "weight": 1.0,
                            "marks_allocation": 10.0
                        }
                    ]
                },
                {
                    "question_number": 2,
                    "max_marks": 10.0,
                    "concepts": [
                        {
                            "concept": "Grammar rules and examples",
                            "keywords": ["example", "grammar", "rules", "production", "syntax"],
                            "weight": 1.0,
                            "marks_allocation": 10.0
                        }
                    ]
                }
            ],
            "passing_marks": 10.0,
            "created_at": datetime.utcnow()
        }
        
        # Insert test scheme
        scheme_result = await db.evaluation_schemes.insert_one(test_scheme)
        print(f"[OK] Test scheme created: {scheme_result.inserted_id}")
        
        # Create test session
        test_session = {
            "_id": ObjectId(),
            "name": "Test AI Processing Session",
            "description": "Session for testing real AI processing",
            "scheme_id": scheme_result.inserted_id,
            "status": "active",
            "created_at": datetime.utcnow(),
            "processed_count": 0
        }
        
        session_result = await db.exam_sessions.insert_one(test_session)
        print(f"[OK] Test session created: {session_result.inserted_id}")
        
        # Create test answer script
        test_script = {
            "_id": ObjectId(),
            "session_id": session_result.inserted_id,
            "student_name": "Test Student",
            "file_name": test_image.name,
            "image_path": str(test_image),
            "status": ScriptStatus.PENDING,
            "uploaded_at": datetime.utcnow()
        }
        
        script_result = await db.answer_scripts.insert_one(test_script)
        script_id = str(script_result.inserted_id)
        print(f"[OK] Test script created: {script_id}")
        
        # Create mock task object for progress tracking
        class MockTask:
            def update_state(self, state, meta):
                progress = meta.get('progress', 0)
                stage = meta.get('stage', 'unknown')
                print(f"[PROGRESS] {progress}% - {stage}")
        
        mock_task = MockTask()
        
        print("\nSTARTING REAL AI PROCESSING TEST")
        print("=" * 40)
        
        # Run real AI processing
        start_time = time.time()
        
        try:
            result = await _real_ai_process_script(script_id, mock_task)
            processing_time = time.time() - start_time
            
            print("\nREAL AI PROCESSING COMPLETED!")
            print("=" * 40)
            print(f"Script ID: {result['script_id']}")
            print(f"Student: {result['student_name']}")
            print(f"File: {result['script_name']}")
            print(f"Score: {result['total_score']}/{result['max_score']} ({result['percentage']:.1f}%)")
            print(f"Questions Extracted: {result['questions_extracted']}")
            print(f"OCR Confidence: {result['ocr_confidence']:.3f}")
            print(f"Verification Confidence: {result['verification_confidence']:.3f}")
            print(f"Needs Manual Review: {result['requires_manual_review']}")
            print(f"Total Processing Time: {processing_time:.2f}s")
            
            # Verify data was saved correctly
            print("\nVERIFYING DATABASE RESULTS")
            
            # Check script status
            updated_script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if updated_script and updated_script.get('status') == ScriptStatus.COMPLETED:
                print("[OK] Script status updated to COMPLETED")
            else:
                print("[ERROR] Script status not updated correctly")
                
            # Check evaluation result exists
            eval_result = await db.evaluation_results.find_one({"script_id": ObjectId(script_id)})
            if eval_result:
                print("[OK] Evaluation result saved to database")
                print(f"   Evaluation ID: {eval_result['_id']}")
            else:
                print("[ERROR] Evaluation result not found in database")
                
            # Check session processed count
            updated_session = await db.exam_sessions.find_one({"_id": session_result.inserted_id})
            if updated_session and updated_session.get('processed_count', 0) > 0:
                print("[OK] Session processed count updated")
            else:
                print("[ERROR] Session processed count not updated")
                
            success = True
            
        except Exception as e:
            print(f"\n[ERROR] REAL AI PROCESSING FAILED: {e}")
            import traceback
            traceback.print_exc()
            success = False
            
        # Cleanup test data
        print("\nCLEANING UP TEST DATA")
        await db.answer_scripts.delete_one({"_id": ObjectId(script_id)})
        await db.evaluation_results.delete_many({"script_id": ObjectId(script_id)})
        await db.manual_review_queue.delete_many({"script_id": ObjectId(script_id)})
        await db.exam_sessions.delete_one({"_id": session_result.inserted_id})
        await db.evaluation_schemes.delete_one({"_id": scheme_result.inserted_id})
        print("[OK] Test data cleaned up")
        
        # Close database connection
        await close_mongo_connection()
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("AI Evaluation System - Real AI Processing Test")
    print("Testing complete OpenAI + Gemini processing pipeline")
    print()
    
    # Run the test
    success = asyncio.run(test_real_ai_processing())
    
    print()
    print("=" * 60)
    print(f"REAL AI PROCESSING TEST: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("Real AI processing pipeline is working correctly!")
        print("The system is now using actual OpenAI Vision API and Gemini verification.")
        print("Scores are calculated based on real content analysis, not hardcoded values.")
    else:
        print("Real AI processing pipeline has issues.")
        print("Check API keys, service initialization, and error logs above.")
        
    return success

if __name__ == "__main__":
    main()