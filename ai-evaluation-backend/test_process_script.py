#!/usr/bin/env python3
"""
Test the simplified process_answer_script task.
"""

import sys
import time
from bson import ObjectId
from app.workers.celery_app_simple import celery_app

def test_process_script():
    """Test the simplified process_answer_script task."""
    print("=" * 60)
    print("TESTING SIMPLIFIED PROCESS_ANSWER_SCRIPT")
    print("=" * 60)
    
    try:
        # Import the simplified task
        from app.workers.evaluation_worker import process_answer_script_simple
        print("[OK] Simplified process script task imported successfully")
        
        # Check if task is registered
        if 'process_answer_script_simple' in celery_app.tasks:
            print("[OK] Task is registered in Celery app")
        else:
            print("[ERROR] Task not found in registered tasks")
            return False
            
        # Use a real script ID from database
        test_script_id = "68b8831be0978d1b576afaa6"  # Real script from database
        
        print(f"\n[INFO] Testing with script ID: {test_script_id}")
        
        # Trigger the task
        print("\n[INFO] Triggering simplified process script task...")
        result = process_answer_script_simple.delay(test_script_id)
        print(f"[OK] Task triggered with ID: {result.id}")
        
        # Monitor task progress
        print("\n[INFO] Monitoring task progress...")
        timeout = 60  # 60 seconds timeout
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            try:
                state = result.state
                info = result.info
                
                if state == 'PROGRESS' and isinstance(info, dict):
                    stage = info.get('stage', 'unknown')
                    progress = info.get('progress', 0)
                    print(f"[PROGRESS] Stage: {stage}, Progress: {progress}%")
                elif state == 'PENDING':
                    print("[WAITING] Task is pending...")
                else:
                    print(f"[STATE] {state}")
                    
            except Exception as e:
                print(f"[WARNING] Could not get task state: {e}")
                
            time.sleep(3)
        
        # Check final result
        if result.ready():
            if result.successful():
                result_data = result.get()
                print("\n[SUCCESS] Task completed successfully!")
                print(f"Result: {result_data}")
                return True
            else:
                print(f"\n[ERROR] Task failed!")
                print(f"State: {result.state}")
                try:
                    result_data = result.get(propagate=False)
                    print(f"Error info: {result_data}")
                except Exception as e:
                    print(f"Could not get error details: {e}")
                    
                if result.traceback:
                    print(f"Traceback: {result.traceback}")
                return False
        else:
            print(f"\n[TIMEOUT] Task did not complete within {timeout} seconds")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to test process script task: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Testing simplified process_answer_script task...")
    
    # Check if worker is active
    try:
        inspector = celery_app.control.inspect()
        active_queues = inspector.active_queues()
        
        if active_queues is None:
            print("[WARNING] No active workers detected")
            print("Make sure to start the simple worker with: python start_simple_worker.py")
            return
        else:
            print("[OK] Worker(s) are active")
            
    except Exception as e:
        print(f"[ERROR] Cannot connect to Celery broker: {e}")
        return
    
    # Run the test
    success = test_process_script()
    
    print("\n" + "=" * 60)
    if success:
        print("[FINAL] SIMPLIFIED PROCESS SCRIPT TEST PASSED!")
        print("The simplified task works. Now we can debug the full task.")
    else:
        print("[FINAL] SIMPLIFIED PROCESS SCRIPT TEST FAILED!")
        print("Check the error messages above.")
    print("=" * 60)

if __name__ == "__main__":
    main()