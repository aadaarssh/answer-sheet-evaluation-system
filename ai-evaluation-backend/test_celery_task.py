#!/usr/bin/env python3
"""
Simple script to test Celery task execution.
This will trigger the test task and monitor its progress.
"""

import sys
import time
from app.workers.celery_app import celery_app

def test_celery_connection():
    """Test basic Celery connection and task triggering."""
    print("=" * 50)
    print("TESTING CELERY TASK EXECUTION")
    print("=" * 50)
    
    try:
        # Import from simple celery app
        from app.workers.celery_app_simple import celery_app
        from app.workers.evaluation_worker import test_task
        print("[OK] Test task imported successfully")
        
        # Check if task is registered
        if 'test_task' in celery_app.tasks:
            print("[OK] Test task is registered in Celery app")
        else:
            print("[ERROR] Test task not found in registered tasks")
            print(f"Available tasks: {list(celery_app.tasks.keys())}")
            return False
            
        # Trigger the task - try both methods
        print("\n[INFO] Triggering test task...")
        
        # Method 1: Direct task call
        try:
            result = test_task.delay("Hello from test trigger!")
            print(f"[OK] Task triggered with ID: {result.id}")
        except Exception as e:
            print(f"[ERROR] Direct task call failed: {e}")
            
            # Method 2: Send task by name
            try:
                result = celery_app.send_task('test_task', args=["Hello from test trigger!"], queue='evaluation')
                print(f"[OK] Task sent by name with ID: {result.id}")
            except Exception as e2:
                print(f"[ERROR] Send task by name also failed: {e2}")
                return False
        
        # Monitor task progress
        print("\n[INFO] Monitoring task progress...")
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            try:
                # Get task state
                state = result.state
                info = result.info
                
                if state == 'PROGRESS':
                    stage = info.get('stage', 'unknown') if isinstance(info, dict) else 'processing'
                    progress = info.get('progress', 0) if isinstance(info, dict) else 0
                    print(f"[PROGRESS] Stage: {stage}, Progress: {progress}%")
                elif state == 'PENDING':
                    print("[WAITING] Task is pending...")
                else:
                    print(f"[STATE] {state}")
                    
            except Exception as e:
                print(f"[WARNING] Could not get task state: {e}")
                
            time.sleep(2)
        
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
        print(f"[ERROR] Failed to test Celery task: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Testing Celery task execution...")
    
    # Test basic connection
    try:
        # Check if we can connect to broker
        inspector = celery_app.control.inspect()
        active_queues = inspector.active_queues()
        
        if active_queues is None:
            print("[WARNING] No active workers detected")
            print("Make sure to start the worker with: python start_worker.py")
            
            # Still try to trigger task
            response = input("\nDo you want to test task triggering anyway? (y/n): ")
            if response.lower() != 'y':
                return
        else:
            print("[OK] Worker(s) are active")
            
    except Exception as e:
        print(f"[ERROR] Cannot connect to Celery broker: {e}")
        print("Make sure Redis is running and worker is started")
        return
    
    # Run the test
    success = test_celery_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("[FINAL] CELERY TEST PASSED!")
        print("The basic Celery setup is working correctly.")
        print("You can now debug the main process_answer_script task.")
    else:
        print("[FINAL] CELERY TEST FAILED!")
        print("Fix the issues above before proceeding.")
    print("=" * 50)

if __name__ == "__main__":
    main()