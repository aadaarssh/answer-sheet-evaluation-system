from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import settings
from ..database import get_database
from ..models.user import User, UserInDB
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email from database."""
    try:
        db = get_database()
        user_doc = await db.users.find_one({"email": email})
        
        if user_doc:
            return UserInDB(**user_doc)
        return None
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID from database."""
    try:
        db = get_database()
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if user_doc:
            return UserInDB(**user_doc)
        return None
    except Exception as e:
        logger.error(f"Error fetching user by ID: {e}")
        return None

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

from pydantic import BaseModel

# Token models for API responses
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None