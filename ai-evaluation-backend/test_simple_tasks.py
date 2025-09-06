#!/usr/bin/env python3
"""
Test the completely separate simple tasks.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_simple_tasks():
    """Test the separate simple tasks."""
    print("=" * 60)
    print("TESTING SEPARATE SIMPLE TASKS")
    print("=" * 60)
    
    try:
        # Import simple celery app
        from app.workers.celery_app_simple import celery_app
        
        # Check registered tasks
        custom_tasks = [t for t in celery_app.tasks.keys() if not t.startswith('celery.')]
        print(f"[INFO] Registered tasks: {custom_tasks}")
        
        # Test 1: debug_task
        print("\n[TEST 1] Testing debug_task...")
        result1 = celery_app.send_task('debug_task', args=["Test debug param"])
        print(f"[OK] debug_task sent with ID: {result1.id}")
        
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
                    print("[WAITING] debug_task is pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(2)
        
        # Check result
        debug_success = False
        if result1.ready():
            if result1.successful():
                data = result1.get()
                print(f"[SUCCESS] debug_task completed: {data}")
                debug_success = True
            else:
                print(f"[ERROR] debug_task failed: {result1.state}")
                if result1.traceback:
                    print(f"Traceback: {result1.traceback}")
        else:
            print("[TIMEOUT] debug_task timed out")
            
        print("\n" + "-" * 60)
        
        # Test 2: script_task
        print("\n[TEST 2] Testing script_task...")
        result2 = celery_app.send_task('script_task', args=["68b8831be0978d1b576afaa6"])
        print(f"[OK] script_task sent with ID: {result2.id}")
        
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
                    print("[WAITING] script_task is pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(2)
        
        # Check result
        script_success = False
        if result2.ready():
            if result2.successful():
                data = result2.get()
                print(f"[SUCCESS] script_task completed: {data}")
                script_success = True
            else:
                print(f"[ERROR] script_task failed: {result2.state}")
                if result2.traceback:
                    print(f"Traceback: {result2.traceback}")
        else:
            print("[TIMEOUT] script_task timed out")
            
        return debug_success and script_success
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_simple_tasks()
    
    print("\n" + "=" * 60)
    if success:
        print("[FINAL] SIMPLE TASKS TEST PASSED!")
        print("The separate task module works correctly")
    else:
        print("[FINAL] SIMPLE TASKS TEST FAILED!")
        print("There may be an issue with task execution or imports")
    print("=" * 60)

if __name__ == "__main__":
    main()