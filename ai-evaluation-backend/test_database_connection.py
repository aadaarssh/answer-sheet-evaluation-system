#!/usr/bin/env python3
"""
Database connection test script
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

async def test_database_connection():
    """Test MongoDB connection."""
    print("=" * 50)
    print("DATABASE CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Test 1: Import configuration
        print("\n1. Testing Configuration...")
        from app.config import settings
        print(f"   [OK] MongoDB URL: {settings.mongodb_url}")
        print(f"   [OK] Database Name: {settings.database_name}")
        
        # Test 2: Test direct MongoDB connection
        print("\n2. Testing MongoDB Connection...")
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient(settings.mongodb_url)
        
        try:
            # Test connection with timeout
            await asyncio.wait_for(client.admin.command('ping'), timeout=5.0)
            print("   [OK] MongoDB connection successful!")
            
            # Test database access
            db = client[settings.database_name]
            collections = await db.list_collection_names()
            print(f"   [OK] Database accessible: {len(collections)} collections found")
            
            if collections:
                print(f"   [INFO] Collections: {', '.join(collections)}")
            else:
                print("   [INFO] Database is empty (this is normal for new installations)")
            
            client.close()
            return True
            
        except asyncio.TimeoutError:
            print("   [ERROR] MongoDB connection timed out")
            print("   [HELP] Is MongoDB running?")
            client.close()
            return False
        except Exception as e:
            print(f"   [ERROR] MongoDB connection failed: {e}")
            client.close()
            return False
            
    except ImportError as e:
        print(f"   [ERROR] Import failed: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
        return False

async def test_app_database_connection():
    """Test app database connection."""
    print("\n3. Testing App Database Connection...")
    try:
        from app.database import connect_to_mongo, get_database, close_mongo_connection
        
        # Test connection
        await connect_to_mongo()
        print("   [OK] App database connection successful!")
        
        # Test database access
        db = get_database()
        result = await db.command('ping')
        print("   [OK] Database accessible via app")
        
        # Close connection
        await close_mongo_connection()
        print("   [OK] Database connection closed cleanly")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] App database connection failed: {e}")
        return False

def print_mongodb_help():
    """Print MongoDB installation and startup help."""
    print("\n" + "=" * 50)
    print("MONGODB INSTALLATION & STARTUP HELP")
    print("=" * 50)
    
    print("\n[OPTION 1] Install MongoDB Community Edition")
    print("   1. Download MongoDB from: https://www.mongodb.com/try/download/community")
    print("   2. Install with default settings")
    print("   3. MongoDB will start automatically as a Windows service")
    
    print("\n[OPTION 2] Use MongoDB Docker Container")
    print("   1. Install Docker Desktop")
    print("   2. Run: docker run -d -p 27017:27017 --name mongodb mongo:latest")
    print("   3. MongoDB will be available at localhost:27017")
    
    print("\n[OPTION 3] Use MongoDB Atlas (Cloud)")
    print("   1. Create free account at https://www.mongodb.com/cloud/atlas")
    print("   2. Create cluster and get connection string")
    print("   3. Update MONGODB_URL in .env file")
    
    print("\n[QUICK START] Commands:")
    print("   - Check if MongoDB is running: mongosh --eval 'db.adminCommand(\"ping\")'")
    print("   - Start MongoDB service: net start MongoDB")
    print("   - Stop MongoDB service: net stop MongoDB")
    print("   - MongoDB default URL: mongodb://localhost:27017")

async def main():
    """Run database connection tests."""
    success1 = await test_database_connection()
    success2 = False
    
    if success1:
        success2 = await test_app_database_connection()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("[SUCCESS] DATABASE CONNECTION SUCCESSFUL!")
        print("\n[READY] Database is ready for the AI evaluation system!")
        print("\nYou can now start the backend server:")
        print("   python start_server.py")
    else:
        print("[FAILED] DATABASE CONNECTION FAILED!")
        print("\n[HELP] MongoDB is not running or not accessible.")
        print_mongodb_help()
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())