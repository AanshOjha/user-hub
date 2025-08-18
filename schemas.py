from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: Optional[str] = None  # Optional for SAML users
    role_id: Optional[int] = None

class UserCreateSAML(UserBase):
    """Schema for creating SAML users"""
    saml_subject_id: str
    azure_role: Optional[str] = None
    role_id: Optional[int] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    azure_role: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    is_saml_user: bool
    saml_subject_id: Optional[str] = None
    azure_role: Optional[str] = None
    role_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class User(UserInDB):
    role: Optional["Role"] = None

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoleWithPermissions(Role):
    permissions: List["Permission"] = []

# Permission schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Audit Log schemas
class AuditLogBase(BaseModel):
    action: str
    resource: str
    details: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    user_id: int

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Dashboard schemas
class UserDashboard(BaseModel):
    user: User
    permissions: List[str]
    recent_activities: List[AuditLog]

# Candidate schemas
class CandidateBase(BaseModel):
    name: str
    email: str

class CandidateCreate(CandidateBase):
    document_path: Optional[str] = None

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    document_path: Optional[str] = None

class Candidate(CandidateBase):
    id: int
    document_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    
    class Config:
        from_attributes = True

# Update forward references
User.model_rebuild()
RoleWithPermissions.model_rebuild()
