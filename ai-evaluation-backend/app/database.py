from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

# Database instance
db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes for performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for performance"""
    try:
        # Users collection indexes
        await db.database.users.create_index("email", unique=True)
        
        # Evaluation schemes indexes
        await db.database.evaluation_schemes.create_index([("professor_id", 1), ("created_at", -1)])
        
        # Exam sessions indexes
        await db.database.exam_sessions.create_index([("professor_id", 1), ("status", 1)])
        
        # Answer scripts indexes
        await db.database.answer_scripts.create_index([("session_id", 1), ("status", 1)])
        
        # Evaluation results indexes
        await db.database.evaluation_results.create_index([("session_id", 1), ("percentage", 1)])
        
        # Manual review queue indexes
        await db.database.manual_review_queue.create_index([("status", 1), ("priority", 1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.database