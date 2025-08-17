from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from database import User as UserModel
import schemas

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds
)
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        return False
    # For SAML users, password authentication is not applicable
    if user.is_saml_user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def authenticate_saml_user(db: Session, email: str):
    """Authenticate user via SAML (no password required)"""
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        return False
    if not user.is_saml_user:
        return False
    return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(UserModel).filter(UserModel.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permission(user: UserModel, resource: str, action: str, db: Session) -> bool:
    """Check if user has specific permission"""
    if not user.role:
        return False
    
    # Import here to avoid circular imports
    from database import RolePermission, Permission
    
    # Get all permissions for the user's role
    permissions = db.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == user.role_id
    ).all()
    
    # Check if user has the specific permission
    for permission in permissions:
        if permission.resource == resource and permission.action == action:
            return True
    
    return False

def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def permission_dependency(
        current_user: UserModel = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if not check_permission(current_user, resource, action, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to {action} {resource}"
            )
        return current_user
    
    return permission_dependency
