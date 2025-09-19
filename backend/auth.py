from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os
from typing import Optional

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")

try:
    mongo_client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        connectTimeoutMS=10000,          # 10 second connection timeout
        socketTimeoutMS=20000,           # 20 second socket timeout
        maxPoolSize=10,                  # Limit connection pool size
        retryWrites=True
    )
    mongo_db = mongo_client[MONGODB_DB]
    users_collection = mongo_db["users"]
    # Test connection
    mongo_client.admin.command('ping')
    print("MongoDB connection successful for auth")
except Exception as e:
    print(f"MongoDB connection failed for auth: {e}")
    mongo_client = None
    mongo_db = None
    users_collection = None

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # Default role is user

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    """Get user by email from MongoDB"""
    if users_collection is None:
        return None
    return users_collection.find_one({"email": email})

def get_user_by_id(user_id: str):
    """Get user by ID from MongoDB"""
    if users_collection is None:
        return None
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None

def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Get current admin user"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Routes
@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """Sign up a new user"""
    if users_collection is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if user_data.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'admin'"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "password": hashed_password,
        "role": user_data.role,
        "created_at": datetime.utcnow()
    }
    
    # Insert user into MongoDB
    result = users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    # Return token and user info
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        role=user_data.role,
        created_at=user_doc["created_at"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user"""
    user = authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])}, expires_delta=access_token_expires
    )
    
    # Return token and user info
    user_response = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
        created_at=user["created_at"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        role=current_user["role"],
        created_at=current_user["created_at"]
    )

@router.get("/admin-only")
async def admin_only_endpoint(current_user: dict = Depends(get_current_admin_user)):
    """Admin only endpoint"""
    return {"message": "This is an admin-only endpoint", "user": current_user["email"]}

# Initialize default admin user
def create_default_admin():
    """Create default admin user if it doesn't exist"""
    if users_collection is None:
        print("MongoDB not available, skipping admin creation")
        return
    
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    
    existing_admin = get_user_by_email(admin_email)
    if not existing_admin:
        admin_doc = {
            "email": admin_email,
            "password": get_password_hash(admin_password),
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(admin_doc)
        print(f"✅ Default admin user created: {admin_email} / {admin_password}")
    else:
        print(f"ℹ️  Admin user already exists: {admin_email}")

# Create default admin on module import
create_default_admin()
