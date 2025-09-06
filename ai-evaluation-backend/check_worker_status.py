#!/usr/bin/env python3
"""
Check current Celery worker status and queue configuration.
"""

from app.workers.celery_app import celery_app

def check_worker_status():
    """Check current worker configuration."""
    print("=" * 60)
    print("CELERY WORKER STATUS CHECK")
    print("=" * 60)
    
    try:
        inspector = celery_app.control.inspect()
        
        # Get worker stats
        stats = inspector.stats()
        if not stats:
            print("[ERROR] No active workers found")
            print("\nTo fix this:")
            print("1. Stop current worker (Ctrl+C)")
            print("2. Restart worker: python start_worker.py")
            print("3. Worker will now listen to: celery, evaluation, batch queues")
            return False
            
        print(f"[OK] Active workers: {len(stats)}")
        for worker_name, worker_stats in stats.items():
            print(f"  - {worker_name} (PID: {worker_stats['pid']})")
        
        # Get active queues
        queues = inspector.active_queues()
        if queues:
            print("\n[INFO] Current queue configuration:")
            for worker_name, worker_queues in queues.items():
                queue_names = [q['name'] for q in worker_queues]
                print(f"  - {worker_name}: {queue_names}")
                
                if 'celery' not in queue_names:
                    print(f"[WARNING] Worker {worker_name} is NOT listening to 'celery' queue")
                    print("This explains why test tasks are stuck in PENDING state")
                    print("\nTO FIX:")
                    print("1. Stop current worker (Ctrl+C in worker terminal)")
                    print("2. Restart worker: python start_worker.py") 
                    print("3. Worker will now listen to all queues including 'celery'")
                    return False
                else:
                    print(f"[OK] Worker {worker_name} is listening to 'celery' queue")
        
        # Get registered tasks
        registered = inspector.registered()
        if registered:
            print(f"\n[INFO] Registered tasks:")
            for worker_name, tasks in registered.items():
                custom_tasks = [t for t in tasks if not t.startswith('celery.')]
                print(f"  - {worker_name}: {custom_tasks}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Could not inspect worker: {e}")
        return False

def main():
    """Main function."""
    success = check_worker_status()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] Worker configuration looks good!")
        print("You can now test tasks with: python test_celery_task.py")
    else:
        print("[ACTION REQUIRED] Worker needs to be restarted")
        print("Follow the instructions above to fix the worker configuration")
    print("=" * 60)

if __name__ == "__main__":
    main()