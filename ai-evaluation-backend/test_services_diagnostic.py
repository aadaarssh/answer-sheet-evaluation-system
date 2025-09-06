#!/usr/bin/env python3
"""
Test service diagnostics to identify initialization issues.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_services_diagnostic():
    """Run service diagnostics to identify the problem."""
    print("=" * 70)
    print("SERVICE DIAGNOSTICS TEST")
    print("=" * 70)
    
    try:
        from app.workers.celery_app_simple import celery_app
        
        # Run service diagnostics
        print("\n[INFO] Running service diagnostics...")
        result = celery_app.send_task('diagnose_services')
        print(f"[OK] Diagnostics task sent with ID: {result.id}")
        
        # Monitor result
        timeout = 60
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            try:
                state = result.state
                if state == 'PROGRESS':
                    info = result.info
                    if isinstance(info, dict):
                        stage = info.get('stage', 'unknown')
                        progress = info.get('progress', 0)
                        print(f"[PROGRESS] {stage} ({progress}%)")
                    else:
                        print(f"[PROGRESS] Processing...")
                elif state == 'PENDING':
                    print("[WAITING] Diagnostics pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(3)
        
        # Get results
        if result.ready():
            if result.successful():
                data = result.get()
                print(f"\n[SUCCESS] Service diagnostics completed!")
                
                # Display detailed results
                print("\n" + "="*60)
                print("SERVICE STATUS REPORT")
                print("="*60)
                
                services = data.get('services', {})
                
                for service_name, status in services.items():
                    if service_name == 'config':
                        print(f"\n{service_name.upper()}:")
                        if isinstance(status, dict):
                            for key, value in status.items():
                                print(f"  {key}: {value}")
                        else:
                            print(f"  {status}")
                    else:
                        status_symbol = "✅" if status == 'SUCCESS' else "❌"
                        print(f"\n{service_name.upper()}: {status_symbol}")
                        if status != 'SUCCESS':
                            print(f"  Error: {status}")
                
                # Identify the problematic service
                failed_services = [name for name, status in services.items() 
                                 if status != 'SUCCESS' and not isinstance(status, dict)]
                
                if failed_services:
                    print(f"\n🔍 PROBLEM IDENTIFIED:")
                    print(f"   Failed services: {', '.join(failed_services)}")
                    print(f"\n💡 SOLUTION:")
                    print("   The main task fails because these services can't initialize.")
                    print("   We can:")
                    print("   1. Fix the service initialization issues")
                    print("   2. Create a version that skips failed services")
                    print("   3. Use mock/fallback versions of failing services")
                else:
                    print(f"\n🤔 All services initialized successfully.")
                    print("   The issue might be in the task execution logic itself.")
                
                return True, failed_services
                
            else:
                print(f"[ERROR] Diagnostics failed: {result.state}")
                if result.traceback:
                    print(f"Traceback: {result.traceback}")
                return False, []
        else:
            print(f"[TIMEOUT] Diagnostics timed out")
            return False, []
            
    except Exception as e:
        print(f"[ERROR] Diagnostic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_minimal_processing():
    """Test minimal processing without problematic services."""
    print(f"\n{'='*70}")
    print("TESTING MINIMAL PROCESSING")
    print('='*70)
    
    try:
        from app.workers.celery_app_simple import celery_app
        
        # Run minimal processing
        result = celery_app.send_task('minimal_process_script', args=["68b8831be0978d1b576afaa6"])
        print(f"[OK] Minimal processing task sent with ID: {result.id}")
        
        # Monitor result
        timeout = 60
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            try:
                state = result.state
                if state == 'PROGRESS':
                    info = result.info
                    if isinstance(info, dict):
                        stage = info.get('stage', 'unknown')
                        progress = info.get('progress', 0)
                        script_id = info.get('script_id', '')
                        print(f"[PROGRESS] {stage} ({progress}%) - {script_id}")
                    else:
                        print(f"[PROGRESS] Processing...")
                elif state == 'PENDING':
                    print("[WAITING] Minimal processing pending...")
                else:
                    print(f"[STATE] {state}")
            except Exception as e:
                print(f"[WARNING] Could not get state: {e}")
                
            time.sleep(3)
        
        # Check result
        if result.ready():
            if result.successful():
                data = result.get()
                print(f"\n[SUCCESS] Minimal processing completed!")
                print(f"  Script: {data.get('script_name', 'unknown')}")
                print(f"  Student: {data.get('student_name', 'unknown')}")
                print(f"  Message: {data.get('message', 'none')}")
                return True
            else:
                print(f"[ERROR] Minimal processing failed: {result.state}")
                if result.traceback:
                    print(f"Traceback: {result.traceback}")
                return False
        else:
            print("[TIMEOUT] Minimal processing timed out")
            return False
            
    except Exception as e:
        print(f"[ERROR] Minimal processing test failed: {e}")
        return False

def main():
    """Main diagnostic function."""
    print("Running comprehensive service diagnostics...")
    print("This will identify exactly which services are causing the main task to fail.")
    
    # Test 1: Service diagnostics
    diagnostic_success, failed_services = test_services_diagnostic()
    
    if diagnostic_success:
        # Test 2: Minimal processing (bypasses service issues)
        minimal_success = test_minimal_processing()
        
        print(f"\n{'='*70}")
        print("DIAGNOSTIC SUMMARY")
        print('='*70)
        
        if failed_services:
            print(f"🔍 ISSUE IDENTIFIED: Service initialization failures")
            print(f"   Failed services: {', '.join(failed_services)}")
        
        if minimal_success:
            print(f"✅ DATABASE AND CORE LOGIC: Working correctly")
        else:
            print(f"❌ DATABASE OR CORE LOGIC: Has issues")
            
        print(f"\n🎯 RECOMMENDATION:")
        if failed_services and minimal_success:
            print("   Create a version of process_answer_script that:")
            print("   1. Skips failed service initialization")
            print("   2. Uses fallback/mock versions for missing services") 
            print("   3. Focuses on core database operations")
        elif not minimal_success:
            print("   Fix the database connection or core logic issues first")
        else:
            print("   The main task failure might be a different issue")
            
    else:
        print(f"\n❌ Could not complete diagnostics")
        print("   Check worker logs for detailed error information")

if __name__ == "__main__":
    main()