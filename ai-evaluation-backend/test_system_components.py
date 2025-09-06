#!/usr/bin/env python3
"""
Comprehensive AI Evaluation System Component Testing

This script tests each component individually to identify exact failure points,
particularly focusing on OCR confidence issues.

Usage: python test_system_components.py
"""

import sys
import os
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self):
        self.results = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "system": "AI Evaluation System",
                "focus": "OCR confidence failure analysis"
            },
            "component_tests": {},
            "performance_metrics": {},
            "summary": {}
        }
        
    def log_test_result(self, component, status, details, metrics=None):
        """Log test result for a component."""
        self.results["component_tests"][component] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if metrics:
            self.results["performance_metrics"][component] = metrics
            
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"\n{status_symbol} {component}: {status}")
        if isinstance(details, dict):
            for key, value in details.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {details}")

    async def test_1_database_connection(self):
        """Test 1: Database Connection and Data Integrity"""
        print("\n" + "="*60)
        print("TEST 1: DATABASE CONNECTION & DATA INTEGRITY")
        print("="*60)
        
        try:
            from app.database import connect_to_mongo, get_database, close_mongo_connection
            from bson import ObjectId
            
            # Connect to database
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                self.log_test_result("database_connection", "FAIL", 
                                    {"error": "Database connection returned None"})
                return False
            
            # Test collections exist
            collections = await db.list_collection_names()
            required_collections = ['answer_scripts', 'exam_sessions', 'evaluation_schemes', 'evaluation_results']
            missing_collections = [col for col in required_collections if col not in collections]
            
            # Count documents
            script_count = await db.answer_scripts.count_documents({})
            session_count = await db.exam_sessions.count_documents({})
            scheme_count = await db.evaluation_schemes.count_documents({})
            
            # Test sample data integrity
            sample_script = await db.answer_scripts.find_one({})
            sample_session = await db.exam_sessions.find_one({}) if sample_script else None
            
            details = {
                "connection": "SUCCESS",
                "collections_found": len(collections),
                "missing_collections": missing_collections if missing_collections else "None",
                "script_count": script_count,
                "session_count": session_count,
                "scheme_count": scheme_count,
                "sample_data": "Found" if sample_script else "Missing"
            }
            
            if sample_script:
                details["sample_script_id"] = str(sample_script["_id"])
                details["sample_file_path"] = sample_script.get("image_path", "Not set")
                details["sample_status"] = sample_script.get("status", "Unknown")
                
                # Check if image file exists
                if "image_path" in sample_script:
                    image_exists = os.path.exists(sample_script["image_path"])
                    details["image_file_exists"] = image_exists
                    if not image_exists:
                        details["image_path_checked"] = sample_script["image_path"]
            
            await close_mongo_connection()
            
            status = "FAIL" if missing_collections or script_count == 0 else "PASS"
            self.log_test_result("database_connection", status, details)
            return status == "PASS"
            
        except Exception as e:
            self.log_test_result("database_connection", "FAIL", 
                               {"error": str(e), "type": type(e).__name__})
            return False

    def test_2_config_and_api_keys(self):
        """Test 2: Configuration and API Keys"""
        print("\n" + "="*60)
        print("TEST 2: CONFIGURATION & API KEYS")
        print("="*60)
        
        try:
            from app.config import settings
            
            details = {
                "mongodb_url": "SET" if settings.mongodb_url else "MISSING",
                "redis_url": "SET" if settings.redis_url else "MISSING",
                "openai_api_key": "SET" if settings.openai_api_key else "MISSING",
                "gemini_api_key": "SET" if settings.gemini_api_key else "MISSING",
                "upload_dir": settings.upload_directory,
                "upload_dir_exists": os.path.exists(settings.upload_directory)
            }
            
            # Test OpenAI API key validity (if set)
            if settings.openai_api_key:
                try:
                    import openai
                    openai.api_key = settings.openai_api_key
                    # Try a simple API call to validate
                    # Note: This is just a key validation, not a full API test
                    details["openai_key_format"] = "VALID" if settings.openai_api_key.startswith('sk-') else "INVALID_FORMAT"
                except Exception as e:
                    details["openai_import_error"] = str(e)
            
            # Check critical missing configurations
            missing_configs = []
            if not settings.mongodb_url:
                missing_configs.append("MONGODB_URL")
            if not settings.openai_api_key:
                missing_configs.append("OPENAI_API_KEY")
            if not settings.gemini_api_key:
                missing_configs.append("GEMINI_API_KEY")
                
            details["missing_critical_configs"] = missing_configs if missing_configs else "None"
            
            status = "FAIL" if missing_configs else "PASS"
            self.log_test_result("config_and_api_keys", status, details)
            return status == "PASS"
            
        except Exception as e:
            self.log_test_result("config_and_api_keys", "FAIL",
                               {"error": str(e), "type": type(e).__name__})
            return False

    def test_3_file_operations(self):
        """Test 3: File Upload and Storage Operations"""
        print("\n" + "="*60)
        print("TEST 3: FILE UPLOAD & STORAGE OPERATIONS")
        print("="*60)
        
        try:
            from app.config import settings
            
            upload_dir = Path(settings.upload_directory)
            test_file_path = upload_dir / "test_file.txt"
            
            # Test directory creation
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Test file write
            test_content = "Test content for system testing"
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            
            # Test file read
            with open(test_file_path, 'r') as f:
                read_content = f.read()
            
            # Test file permissions
            file_readable = os.access(test_file_path, os.R_OK)
            file_writable = os.access(test_file_path, os.W_OK)
            
            # Check existing uploaded files
            existing_files = list(upload_dir.glob("*"))
            image_files = list(upload_dir.glob("*.jpg")) + list(upload_dir.glob("*.png")) + list(upload_dir.glob("*.jpeg"))
            
            # Clean up test file
            test_file_path.unlink()
            
            details = {
                "upload_directory": str(upload_dir),
                "directory_exists": upload_dir.exists(),
                "directory_writable": os.access(upload_dir, os.W_OK),
                "test_file_write": "SUCCESS" if read_content == test_content else "FAILED",
                "file_permissions": f"R:{file_readable} W:{file_writable}",
                "existing_files_count": len(existing_files),
                "image_files_count": len(image_files),
                "sample_image_files": [f.name for f in image_files[:3]]  # Show first 3
            }
            
            status = "PASS" if upload_dir.exists() and read_content == test_content else "FAIL"
            self.log_test_result("file_operations", status, details)
            return status == "PASS"
            
        except Exception as e:
            self.log_test_result("file_operations", "FAIL",
                               {"error": str(e), "type": type(e).__name__})
            return False

    async def test_4_ocr_service(self):
        """Test 4: OpenAI Vision API OCR Extraction - CRITICAL TEST"""
        print("\n" + "="*60)
        print("TEST 4: OPENAI VISION API OCR EXTRACTION [CRITICAL]")
        print("="*60)
        
        try:
            start_time = time.time()
            
            # Find test images
            from app.config import settings
            upload_dir = Path(settings.upload_directory)
            image_files = list(upload_dir.glob("*.jpg")) + list(upload_dir.glob("*.png")) + list(upload_dir.glob("*.jpeg"))
            
            if not image_files:
                self.log_test_result("ocr_service", "FAIL",
                                   {"error": "No image files found in upload directory",
                                    "upload_dir": str(upload_dir),
                                    "searched_extensions": ["jpg", "png", "jpeg"]})
                return False
            
            # Test OCR Service import and initialization
            try:
                from app.services.ocr_service import OCRService
                ocr_service = OCRService()
                service_init = "SUCCESS"
            except Exception as e:
                self.log_test_result("ocr_service", "FAIL",
                                   {"error": f"OCR Service initialization failed: {e}",
                                    "import_error": str(e)})
                return False
            
            # Test with first available image
            test_image = image_files[0]
            
            try:
                # Call OCR extraction
                questions, confidence = await ocr_service.extract_and_segment_questions(str(test_image))
                
                processing_time = time.time() - start_time
                
                details = {
                    "service_initialization": service_init,
                    "test_image": test_image.name,
                    "image_size": f"{test_image.stat().st_size} bytes",
                    "image_exists": test_image.exists(),
                    "questions_extracted": len(questions) if questions else 0,
                    "ocr_confidence": confidence,
                    "processing_time_seconds": round(processing_time, 2)
                }
                
                # Detailed analysis of results
                if questions:
                    details["sample_question"] = {
                        "number": questions[0].question_number if hasattr(questions[0], 'question_number') else "Unknown",
                        "text_length": len(questions[0].raw_text) if hasattr(questions[0], 'raw_text') else 0,
                        "text_preview": (questions[0].raw_text[:100] + "...") if hasattr(questions[0], 'raw_text') and len(questions[0].raw_text) > 100 else str(questions[0])
                    }
                
                # This is the CRITICAL test for OCR confidence
                if confidence == 0:
                    details["critical_issue"] = "OCR CONFIDENCE IS 0 - TEXT EXTRACTION FAILED"
                    details["likely_causes"] = [
                        "OpenAI API key invalid or expired",
                        "Image format not supported",
                        "Image quality too poor",
                        "OpenAI service error",
                        "Network connectivity issue"
                    ]
                    status = "FAIL"
                elif confidence < 0.5:
                    details["warning"] = "LOW OCR CONFIDENCE - POOR TEXT EXTRACTION"
                    status = "PARTIAL"
                else:
                    details["success"] = "OCR EXTRACTION WORKING CORRECTLY"
                    status = "PASS"
                
                self.log_test_result("ocr_service", status, details,
                                   {"processing_time": processing_time,
                                    "confidence": confidence,
                                    "questions_count": len(questions) if questions else 0})
                
                return status == "PASS"
                
            except Exception as ocr_error:
                processing_time = time.time() - start_time
                
                details = {
                    "service_initialization": service_init,
                    "test_image": test_image.name,
                    "ocr_error": str(ocr_error),
                    "error_type": type(ocr_error).__name__,
                    "processing_time_seconds": round(processing_time, 2),
                    "critical_failure": "OCR SERVICE FAILED TO PROCESS IMAGE"
                }
                
                # Analyze specific error types
                if "API key" in str(ocr_error):
                    details["root_cause"] = "OpenAI API key issue"
                elif "network" in str(ocr_error).lower() or "connection" in str(ocr_error).lower():
                    details["root_cause"] = "Network connectivity issue"
                elif "format" in str(ocr_error).lower() or "image" in str(ocr_error).lower():
                    details["root_cause"] = "Image format or quality issue"
                else:
                    details["root_cause"] = "Unknown OCR service error"
                
                self.log_test_result("ocr_service", "FAIL", details,
                                   {"processing_time": processing_time})
                return False
                
        except Exception as e:
            self.log_test_result("ocr_service", "FAIL",
                               {"error": str(e), "type": type(e).__name__,
                                "test_phase": "Service setup"})
            return False

    async def test_5_gemini_verification(self):
        """Test 5: Gemini API Verification Service"""
        print("\n" + "="*60)
        print("TEST 5: GEMINI API VERIFICATION SERVICE")
        print("="*60)
        
        try:
            start_time = time.time()
            
            # Test Gemini service initialization
            try:
                from app.services.verification_service import VerificationService
                verification_service = VerificationService()
                service_init = "SUCCESS"
            except Exception as e:
                self.log_test_result("gemini_verification", "FAIL",
                                   {"error": f"Verification Service initialization failed: {e}",
                                    "import_error": str(e)})
                return False
            
            # Create mock evaluation result for testing
            from app.models.evaluation import EvaluationResult, QuestionResult
            from app.models.scheme import EvaluationScheme
            
            mock_question_result = QuestionResult(
                question_number=1,
                student_answer="Sample student answer for testing",
                correct_answer="Sample correct answer",
                score=8,
                max_score=10,
                feedback="Good attempt"
            )
            
            mock_evaluation = EvaluationResult(
                script_id=None,
                session_id=None,
                total_score=8,
                max_possible_score=10,
                percentage=80.0,
                question_results=[mock_question_result],
                requires_manual_review=False
            )
            
            mock_scheme = EvaluationScheme(
                name="Test Scheme",
                subject="Test Subject",
                questions=[],
                total_marks=10
            )
            
            mock_student_answers = {1: "Sample student answer for testing"}
            
            try:
                # Test verification
                verification = await verification_service.verify_evaluation(
                    mock_evaluation, mock_scheme, mock_student_answers
                )
                
                processing_time = time.time() - start_time
                
                details = {
                    "service_initialization": service_init,
                    "verification_completed": "SUCCESS",
                    "has_confidence_score": hasattr(verification, 'confidence_score'),
                    "has_flagged_review": hasattr(verification, 'flagged_for_review'),
                    "processing_time_seconds": round(processing_time, 2)
                }
                
                if hasattr(verification, 'confidence_score'):
                    details["confidence_score"] = getattr(verification, 'confidence_score', 'Not available')
                
                if hasattr(verification, 'flagged_for_review'):
                    details["flagged_for_review"] = getattr(verification, 'flagged_for_review', 'Not available')
                
                self.log_test_result("gemini_verification", "PASS", details,
                                   {"processing_time": processing_time})
                return True
                
            except Exception as gemini_error:
                processing_time = time.time() - start_time
                
                details = {
                    "service_initialization": service_init,
                    "gemini_error": str(gemini_error),
                    "error_type": type(gemini_error).__name__,
                    "processing_time_seconds": round(processing_time, 2)
                }
                
                # Analyze error types
                if "API key" in str(gemini_error):
                    details["root_cause"] = "Gemini API key issue"
                elif "quota" in str(gemini_error).lower():
                    details["root_cause"] = "API quota exceeded"
                else:
                    details["root_cause"] = "Gemini service error"
                
                self.log_test_result("gemini_verification", "FAIL", details,
                                   {"processing_time": processing_time})
                return False
                
        except Exception as e:
            self.log_test_result("gemini_verification", "FAIL",
                               {"error": str(e), "type": type(e).__name__})
            return False

    def test_6_celery_tasks(self):
        """Test 6: Celery Task Execution"""
        print("\n" + "="*60)
        print("TEST 6: CELERY TASK EXECUTION")
        print("="*60)
        
        try:
            from app.workers.celery_app_simple import celery_app
            
            # Test Celery app configuration
            broker_url = celery_app.conf.broker_url
            backend_url = celery_app.conf.result_backend
            
            # Test task registration
            custom_tasks = [task for task in celery_app.tasks.keys() if not task.startswith('celery.')]
            
            # Test Redis connection
            redis_connected = False
            try:
                import redis
                r = redis.Redis.from_url(broker_url)
                r.ping()
                redis_connected = True
            except Exception as redis_error:
                redis_error_msg = str(redis_error)
            
            # Test worker availability
            inspector = celery_app.control.inspect()
            active_workers = inspector.stats() or {}
            
            details = {
                "celery_app_loaded": "SUCCESS",
                "broker_url": broker_url,
                "backend_url": backend_url,
                "redis_connected": redis_connected,
                "custom_tasks_count": len(custom_tasks),
                "key_tasks_available": [
                    "process_answer_script" in custom_tasks,
                    "minimal_working_script" in custom_tasks,
                    "test_task" in custom_tasks
                ],
                "active_workers_count": len(active_workers),
                "worker_names": list(active_workers.keys()) if active_workers else "None"
            }
            
            if not redis_connected:
                details["redis_error"] = redis_error_msg
            
            # Test basic task execution if workers are available
            if active_workers:
                try:
                    result = celery_app.send_task('test_task', args=['System test'])
                    time.sleep(3)  # Wait for execution
                    
                    if result.ready():
                        if result.successful():
                            details["test_task_execution"] = "SUCCESS"
                            details["test_task_result"] = "Task completed successfully"
                        else:
                            details["test_task_execution"] = "FAILED"
                            details["test_task_error"] = str(result.info)
                    else:
                        details["test_task_execution"] = "PENDING"
                        details["test_task_note"] = "Task still running"
                        
                except Exception as task_error:
                    details["test_task_execution"] = "ERROR"
                    details["test_task_error"] = str(task_error)
            
            # Determine overall status
            status = "PASS" if (redis_connected and active_workers and 
                              "process_answer_script" in custom_tasks) else "FAIL"
            
            self.log_test_result("celery_tasks", status, details)
            return status == "PASS"
            
        except Exception as e:
            self.log_test_result("celery_tasks", "FAIL",
                               {"error": str(e), "type": type(e).__name__})
            return False

    async def test_7_end_to_end_pipeline(self):
        """Test 7: End-to-End Pipeline Test"""
        print("\n" + "="*60)
        print("TEST 7: END-TO-END PIPELINE TEST")
        print("="*60)
        
        try:
            start_time = time.time()
            
            # Get a test script from database
            from app.database import connect_to_mongo, get_database, close_mongo_connection
            from app.workers.celery_app_simple import celery_app
            
            await connect_to_mongo()
            db = get_database()
            
            # Find a pending script to test with
            test_script = await db.answer_scripts.find_one({"status": "pending"})
            if not test_script:
                test_script = await db.answer_scripts.find_one({})
            
            await close_mongo_connection()
            
            if not test_script:
                self.log_test_result("end_to_end_pipeline", "FAIL",
                                   {"error": "No test scripts available in database"})
                return False
            
            script_id = str(test_script["_id"])
            
            # Test the working task
            try:
                result = celery_app.send_task('minimal_working_script', args=[script_id])
                
                # Wait for completion with timeout
                timeout = 30
                wait_time = 0
                while not result.ready() and wait_time < timeout:
                    time.sleep(1)
                    wait_time += 1
                
                processing_time = time.time() - start_time
                
                if result.ready():
                    if result.successful():
                        task_result = result.get()
                        
                        details = {
                            "pipeline_execution": "SUCCESS",
                            "test_script_id": script_id,
                            "script_found": task_result.get("script_found", False),
                            "student_name": task_result.get("student_name", "Unknown"),
                            "script_name": task_result.get("script_name", "Unknown"),
                            "processing_time_seconds": round(processing_time, 2),
                            "task_result_keys": list(task_result.keys())
                        }
                        
                        status = "PASS"
                        
                    else:
                        details = {
                            "pipeline_execution": "FAILED",
                            "test_script_id": script_id,
                            "task_error": str(result.info),
                            "task_state": result.state,
                            "processing_time_seconds": round(processing_time, 2)
                        }
                        
                        status = "FAIL"
                else:
                    details = {
                        "pipeline_execution": "TIMEOUT",
                        "test_script_id": script_id,
                        "timeout_seconds": timeout,
                        "processing_time_seconds": round(processing_time, 2)
                    }
                    
                    status = "FAIL"
                
                self.log_test_result("end_to_end_pipeline", status, details,
                                   {"processing_time": processing_time})
                
                return status == "PASS"
                
            except Exception as pipeline_error:
                processing_time = time.time() - start_time
                
                self.log_test_result("end_to_end_pipeline", "FAIL",
                                   {"error": str(pipeline_error),
                                    "error_type": type(pipeline_error).__name__,
                                    "processing_time_seconds": round(processing_time, 2)})
                return False
                
        except Exception as e:
            self.log_test_result("end_to_end_pipeline", "FAIL",
                               {"error": str(e), "type": type(e).__name__})
            return False

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SYSTEM TEST REPORT")
        print("="*80)
        
        # Count results
        total_tests = len(self.results["component_tests"])
        passed_tests = sum(1 for result in self.results["component_tests"].values() 
                          if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.results["component_tests"].values() 
                          if result["status"] == "FAIL")
        partial_tests = sum(1 for result in self.results["component_tests"].values() 
                           if result["status"] == "PARTIAL")
        
        # Overall system health
        overall_status = "HEALTHY" if failed_tests == 0 else "DEGRADED" if passed_tests > failed_tests else "CRITICAL"
        
        print(f"\nOVERALL SYSTEM STATUS: {overall_status}")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Tests Failed: {failed_tests}/{total_tests}")
        print(f"Tests Partial: {partial_tests}/{total_tests}")
        
        # Critical findings
        print(f"\n🔍 CRITICAL FINDINGS:")
        
        ocr_test = self.results["component_tests"].get("ocr_service", {})
        if ocr_test.get("status") == "FAIL":
            print(f"❌ OCR CONFIDENCE IS 0 - ROOT CAUSE IDENTIFIED")
            ocr_details = ocr_test.get("details", {})
            if "root_cause" in ocr_details:
                print(f"   Root Cause: {ocr_details['root_cause']}")
            if "critical_issue" in ocr_details:
                print(f"   Issue: {ocr_details['critical_issue']}")
            if "likely_causes" in ocr_details:
                print(f"   Likely Causes:")
                for cause in ocr_details["likely_causes"]:
                    print(f"     - {cause}")
        
        # Component status summary
        print(f"\n📋 COMPONENT STATUS:")
        for component, result in self.results["component_tests"].items():
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {component.replace('_', ' ').title()}: {result['status']}")
        
        # Performance metrics
        if self.results["performance_metrics"]:
            print(f"\n⏱️ PERFORMANCE METRICS:")
            for component, metrics in self.results["performance_metrics"].items():
                if "processing_time" in metrics:
                    print(f"   {component}: {metrics['processing_time']:.2f}s")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if ocr_test.get("status") == "FAIL":
            print("   1. Fix OCR service - this is blocking all evaluations")
            print("   2. Verify OpenAI API key is valid and has credits")
            print("   3. Check image file quality and format")
            print("   4. Test network connectivity to OpenAI services")
        
        if self.results["component_tests"].get("config_and_api_keys", {}).get("status") == "FAIL":
            print("   5. Review configuration file and environment variables")
            print("   6. Ensure all required API keys are set")
        
        if self.results["component_tests"].get("celery_tasks", {}).get("status") == "FAIL":
            print("   7. Start Celery worker: python start_simple_worker.py")
            print("   8. Ensure Redis server is running")
        
        # Save detailed report
        report_path = "system_test_report.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved: {report_path}")
        except Exception as e:
            print(f"\n❌ Could not save report: {e}")
        
        self.results["summary"] = {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "partial_tests": partial_tests,
            "ocr_service_working": ocr_test.get("status") == "PASS"
        }
        
        return overall_status == "HEALTHY"

    async def run_all_tests(self):
        """Run all system component tests"""
        print("🔬 AI EVALUATION SYSTEM - COMPREHENSIVE COMPONENT TESTING")
        print("Focus: Identifying OCR confidence failure and system issues")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all tests in sequence
            await self.test_1_database_connection()
            self.test_2_config_and_api_keys()
            self.test_3_file_operations()
            await self.test_4_ocr_service()  # CRITICAL TEST
            await self.test_5_gemini_verification()
            self.test_6_celery_tasks()
            await self.test_7_end_to_end_pipeline()
            
            # Generate comprehensive report
            success = self.generate_summary_report()
            
            return success
            
        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted by user")
            return False
        except Exception as e:
            print(f"\n💥 Testing failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main testing function"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print(f"\n🎉 All tests passed! System is healthy.")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Check the report above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)