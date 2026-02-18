"""Authentication routes for user registration and login."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.db.connection import get_database
from app.models.user import UserCreate, UserInDB, UserLogin, UserResponse, TokenResponse

# Setup router
router = APIRouter()

# Security utilities
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    
    # Add token ID for revocation capability
    to_encode.update({
        "jti": str(uuid4()),  # JWT ID
        "iat": datetime.now(timezone.utc),  # Issued at
        "iss": "media-manager-api"  # Issuer
    })
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)) -> UserInDB:
    """
    Authentication middleware to get current user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user_doc = await db.users.find_one({"username": username})
    if user_doc is None:
        raise credentials_exception
    
    return UserInDB(**user_doc)

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Get current active user (can be extended to check if user is disabled/banned).
    """
    # For now, all users are considered active
    # In the future, you could add an 'is_active' field to the user model
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db=Depends(get_database)):
    """Register a new user."""
    # Check if username exists
    if await db.users.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user document
    user_in_db = UserInDB(
        **user_data.model_dump(exclude={"password"}),
        password_hash=get_password_hash(user_data.password)
    )
    
    try:
        await db.users.insert_one(user_in_db.model_dump(exclude_none=True))
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    return UserResponse(**user_in_db.model_dump(exclude={"password_hash"}))

@router.post("/login", response_model=TokenResponse)
async def login(form_data: UserLogin, db=Depends(get_database)):
    """Authenticate user and return JWT token."""
    # Find user
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserInDB(**user_doc)
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username}
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout endpoint - in a stateless JWT system, logout is handled client-side
    by removing the token. This endpoint can be used for logging purposes.
    """
    return {"message": f"User {current_user.username} logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(**current_user.model_dump(exclude={"password_hash"}))

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Refresh the access token for the current user.
    This creates a new token with a fresh expiration time.
    """
    access_token = create_access_token(
        data={"sub": current_user.username}
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")
