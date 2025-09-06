#!/usr/bin/env python3
"""
Check what scripts exist in the database for testing.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.database import connect_to_mongo, get_database, close_mongo_connection

async def check_scripts():
    """Check existing scripts in database."""
    try:
        print("=" * 50)
        print("CHECKING DATABASE SCRIPTS")
        print("=" * 50)
        
        # Connect to database
        await connect_to_mongo()
        db = get_database()
        
        # Get all answer scripts
        scripts = await db.answer_scripts.find({}).to_list(length=10)
        
        if scripts:
            print(f"[OK] Found {len(scripts)} scripts in database:")
            for i, script in enumerate(scripts, 1):
                print(f"  {i}. ID: {script['_id']}")
                print(f"     File: {script.get('file_name', 'Unknown')}")
                print(f"     Status: {script.get('status', 'Unknown')}")
                print(f"     Student: {script.get('student_name', 'Unknown')}")
                print()
                
            # Return the first script ID for testing
            test_script_id = str(scripts[0]['_id'])
            print(f"[INFO] Use this script ID for testing: {test_script_id}")
            
        else:
            print("[INFO] No scripts found in database")
            print("You can test with a dummy ObjectId: 66d8b88c098f9cf8f0c57611")
            test_script_id = "66d8b88c098f9cf8f0c57611"
            
        # Also check sessions
        sessions = await db.exam_sessions.find({}).to_list(length=5)
        print(f"[INFO] Found {len(sessions)} exam sessions in database")
        
        # Check schemes
        schemes = await db.evaluation_schemes.find({}).to_list(length=5)
        print(f"[INFO] Found {len(schemes)} evaluation schemes in database")
        
        await close_mongo_connection()
        
        return test_script_id
        
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")
        return None

def main():
    """Main function."""
    script_id = asyncio.run(check_scripts())
    
    if script_id:
        print("=" * 50)
        print("TO TEST THE SIMPLIFIED TASK:")
        print(f"python test_process_script.py")
        print("=" * 50)

if __name__ == "__main__":
    main()