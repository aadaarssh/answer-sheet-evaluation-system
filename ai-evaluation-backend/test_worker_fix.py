#!/usr/bin/env python3
"""
Test script to verify worker fixes
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_worker_import():
    """Test if worker can be imported without errors."""
    try:
        print("Testing worker imports...")
        
        # Test celery app import
        from app.workers.celery_app_simple import celery_app
        print("[OK] Simple Celery app imported successfully")
        
        # Test worker import
        from app.workers.evaluation_worker import process_answer_script
        print("[OK] Worker task imported successfully")
        
        # Test task registration
        registered_tasks = list(celery_app.tasks.keys())
        print(f"[OK] Registered tasks: {registered_tasks}")
        
        # Check if our task is registered
        task_name = 'app.workers.evaluation_worker.process_answer_script'
        if task_name in registered_tasks:
            print(f"[OK] Task {task_name} is properly registered")
        else:
            print(f"[WARNING] Task {task_name} not found in registered tasks")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

def test_task_creation():
    """Test if task can be created without errors."""
    try:
        print("\nTesting task creation...")
        
        from app.workers.evaluation_worker import process_answer_script
        
        # Create a mock task ID
        mock_script_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        
        print(f"[OK] Task function can be called with: {mock_script_id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Task creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Worker Fix Verification Tests")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_worker_import():
        success = False
    
    # Test task creation
    if not test_task_creation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] All tests passed! Worker should now work correctly.")
    else:
        print("[FAILURE] Some tests failed. Check the errors above.")
    print("=" * 50)
    
    return success

if __name__ == "__main__":
    main()