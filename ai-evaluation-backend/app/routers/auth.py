from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..config import settings
from ..database import get_database
from ..models.user import UserCreate, User, UserInDB
from ..utils.auth import (
    authenticate_user, create_access_token, get_password_hash,
    get_current_active_user, Token, get_user_by_email
)
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    """Register a new user."""
    try:
        db = get_database()
        
        # Check if user already exists
        existing_user = await get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user.password)
        user_dict = user.dict()
        del user_dict['password']
        user_dict['hashed_password'] = hashed_password
        
        # Insert user into database
        result = await db.users.insert_one(user_dict)
        
        # Retrieve created user
        created_user = await db.users.find_one({"_id": result.inserted_id})
        
        return User(**created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user information."""
    return User(**current_user.dict())

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: UserInDB = Depends(get_current_active_user)):
    """Refresh access token."""
    try:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(current_user.id)}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )