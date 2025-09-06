#!/usr/bin/env python3
"""
Test the database-enabled simple task.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_db_simple():
    """Test database-enabled simple task."""
    print("=" * 60)
    print("TESTING DATABASE-ENABLED SIMPLE TASK")
    print("=" * 60)
    
    try:
        from app.workers.celery_app_simple import celery_app
        
        # Send task by name to ensure we get the latest version
        print("\n[INFO] Triggering process_answer_script_simple...")
        result = celery_app.send_task(
            'process_answer_script_simple',
            args=["68b8831be0978d1b576afaa6"]
        )
        print(f"[OK] Task triggered with ID: {result.id}")
        
        # Monitor result
        timeout = 60
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            try:
                state = result.state
                if state == 'PROGRESS':
                    info = result.info
                    stage = info.get('stage', 'unknown') if isinstance(info, dict) else 'processing'
                    progress = info.get('progress', 0) if isinstance(info, dict) else 0
                    script_id = info.get('script_id', '') if isinstance(info, dict) else ''
                    print(f"[PROGRESS] Stage: {stage}, Progress: {progress}%, Script: {script_id}")
                elif state == 'PENDING':
                    print("[WAITING] Task is pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(3)
        
        # Check result
        if result.ready():
            if result.successful():
                data = result.get()
                print(f"\n[SUCCESS] Task completed successfully!")
                print(f"Result: {data}")
                return True
            else:
                print(f"\n[ERROR] Task failed: {result.state}")
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
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_db_simple()
    
    print("\n" + "=" * 60)
    if success:
        print("[FINAL] DATABASE SIMPLE TASK TEST PASSED!")
        print("Database connectivity works in worker process")
    else:
        print("[FINAL] DATABASE SIMPLE TASK TEST FAILED!")
        print("Check the error messages above")
    print("=" * 60)

if __name__ == "__main__":
    main()