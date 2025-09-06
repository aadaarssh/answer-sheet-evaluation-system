#!/usr/bin/env python3
"""
Test tasks by sending them directly through the simple Celery app.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_direct_task_call():
    """Test calling task directly through celery app."""
    print("=" * 60)
    print("TESTING DIRECT TASK CALL")
    print("=" * 60)
    
    try:
        # Import simple celery app
        from app.workers.celery_app_simple import celery_app
        
        # Test 1: Send test_task by name
        print("\n[TEST 1] Sending test_task by name...")
        result1 = celery_app.send_task('test_task', args=["Direct test call"])
        print(f"[OK] test_task sent with ID: {result1.id}")
        
        # Monitor result
        timeout = 30
        start_time = time.time()
        
        while not result1.ready() and (time.time() - start_time) < timeout:
            try:
                state = result1.state
                if state == 'PROGRESS':
                    info = result1.info
                    stage = info.get('stage', 'unknown') if isinstance(info, dict) else 'processing'
                    progress = info.get('progress', 0) if isinstance(info, dict) else 0
                    print(f"[PROGRESS] Stage: {stage}, Progress: {progress}%")
                elif state == 'PENDING':
                    print("[WAITING] test_task is pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(2)
        
        # Check result
        if result1.ready():
            if result1.successful():
                data = result1.get()
                print(f"[SUCCESS] test_task completed: {data}")
            else:
                print(f"[ERROR] test_task failed: {result1.state}")
                if result1.traceback:
                    print(f"Traceback: {result1.traceback}")
        else:
            print("[TIMEOUT] test_task timed out")
            
        print("\n" + "-" * 60)
        
        # Test 2: Send process_answer_script_simple by name
        print("\n[TEST 2] Sending process_answer_script_simple by name...")
        result2 = celery_app.send_task(
            'process_answer_script_simple', 
            args=["68b8831be0978d1b576afaa6"]
        )
        print(f"[OK] process_answer_script_simple sent with ID: {result2.id}")
        
        # Monitor result
        start_time = time.time()
        
        while not result2.ready() and (time.time() - start_time) < timeout:
            try:
                state = result2.state
                if state == 'PROGRESS':
                    info = result2.info
                    stage = info.get('stage', 'unknown') if isinstance(info, dict) else 'processing'
                    progress = info.get('progress', 0) if isinstance(info, dict) else 0
                    print(f"[PROGRESS] Stage: {stage}, Progress: {progress}%")
                elif state == 'PENDING':
                    print("[WAITING] process_answer_script_simple is pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(2)
        
        # Check result
        if result2.ready():
            if result2.successful():
                data = result2.get()
                print(f"[SUCCESS] process_answer_script_simple completed: {data}")
                return True
            else:
                print(f"[ERROR] process_answer_script_simple failed: {result2.state}")
                if result2.traceback:
                    print(f"Traceback: {result2.traceback}")
                return False
        else:
            print("[TIMEOUT] process_answer_script_simple timed out")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_direct_task_call()
    
    print("\n" + "=" * 60)
    if success:
        print("[FINAL] DIRECT TASK TEST PASSED!")
        print("The simple configuration works for sending tasks directly")
    else:
        print("[FINAL] DIRECT TASK TEST FAILED!")
        print("There may be a fundamental issue with the worker or task execution")
    print("=" * 60)

if __name__ == "__main__":
    main()