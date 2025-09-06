#!/usr/bin/env python3
"""
Final comprehensive test of the complete pipeline.
Run this after restarting the worker to test everything.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_complete_pipeline():
    """Test the complete processing pipeline."""
    print("=" * 70)
    print("FINAL COMPREHENSIVE PIPELINE TEST")
    print("=" * 70)
    
    try:
        from app.workers.celery_app_simple import celery_app
        
        # Check registered tasks
        custom_tasks = [t for t in celery_app.tasks.keys() if not t.startswith('celery.')]
        print(f"[INFO] Available tasks: {custom_tasks}")
        
        # Test 1: Basic test_task (should work)
        print(f"\n{'='*50}")
        print("TEST 1: BASIC TEST TASK")
        print('='*50)
        
        result1 = celery_app.send_task('test_task', args=["Final pipeline test"])
        print(f"[OK] test_task sent with ID: {result1.id}")
        
        success1 = monitor_task(result1, "test_task", 30)
        
        # Test 2: Database test task (new)
        print(f"\n{'='*50}")
        print("TEST 2: DATABASE CONNECTIVITY TEST")
        print('='*50)
        
        result2 = celery_app.send_task('database_test_task', args=["68b8831be0978d1b576afaa6"])
        print(f"[OK] database_test_task sent with ID: {result2.id}")
        
        success2 = monitor_task(result2, "database_test_task", 60)
        
        # Test 3: Fixed process_answer_script (if worker restarted)
        print(f"\n{'='*50}")
        print("TEST 3: FIXED PROCESS_ANSWER_SCRIPT")
        print('='*50)
        
        result3 = celery_app.send_task('process_answer_script', args=["68b8831be0978d1b576afaa6"])
        print(f"[OK] process_answer_script sent with ID: {result3.id}")
        
        success3 = monitor_task(result3, "process_answer_script", 120)
        
        # Summary
        print(f"\n{'='*70}")
        print("FINAL TEST RESULTS")
        print('='*70)
        
        results = {
            "Basic test_task": "PASS" if success1 else "FAIL",
            "Database connectivity": "PASS" if success2 else "FAIL", 
            "Main process_answer_script": "PASS" if success3 else "FAIL"
        }
        
        for test_name, status in results.items():
            print(f"  {test_name:.<30} {status}")
            
        all_passed = all([success1, success2, success3])
        
        if all_passed:
            print(f"\n[SUCCESS] ALL TESTS PASSED!")
            print("The complete pipeline is working correctly!")
        else:
            print(f"\n[PARTIAL] Some tests failed.")
            if success2:
                print("Database connectivity works - main task issue may be in services initialization")
            else:
                print("Database connectivity failed - need to investigate connection setup")
                
        return all_passed
            
    except Exception as e:
        print(f"[ERROR] Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_task(result, task_name, timeout):
    """Monitor a task execution and return success status."""
    start_time = time.time()
    
    while not result.ready() and (time.time() - start_time) < timeout:
        try:
            state = result.state
            if state == 'PROGRESS':
                info = result.info
                if isinstance(info, dict):
                    stage = info.get('stage', 'unknown')
                    progress = info.get('progress', 0)
                    print(f"[PROGRESS] {task_name}: {stage} ({progress}%)")
                else:
                    print(f"[PROGRESS] {task_name}: processing")
            elif state == 'PENDING':
                print(f"[WAITING] {task_name} pending...")
            else:
                print(f"[STATE] {task_name}: {state}")
        except Exception as e:
            print(f"[WARNING] Could not get {task_name} state: {e}")
            
        time.sleep(3)
    
    # Check final result
    if result.ready():
        if result.successful():
            data = result.get()
            print(f"[SUCCESS] {task_name} completed!")
            if isinstance(data, dict) and 'message' in data:
                print(f"  Message: {data['message']}")
            return True
        else:
            print(f"[ERROR] {task_name} failed: {result.state}")
            if result.traceback:
                print(f"  Traceback: {result.traceback[:200]}...")
            return False
    else:
        print(f"[TIMEOUT] {task_name} timed out after {timeout} seconds")
        return False

def main():
    """Main test function."""
    print("Starting comprehensive pipeline test...")
    print("Make sure the simple worker is running: python start_simple_worker.py")
    
    response = input("\nPress Enter to start tests (or 'q' to quit): ")
    if response.lower() == 'q':
        return
        
    success = test_complete_pipeline()
    
    print("\n" + "=" * 70)
    if success:
        print("CONGRATULATIONS! The complete AI evaluation pipeline is working!")
        print("\nYou can now:")
        print("1. Upload files through the frontend")
        print("2. Tasks will be processed by the worker")
        print("3. Results will be stored in the database")
    else:
        print("Some issues remain. Check the test output above for details.")
    print("=" * 70)

if __name__ == "__main__":
    main()