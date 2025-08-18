from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    # Core fields for both SAML and normal users
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)  # Primary human-readable ID
    full_name = Column(String, nullable=False)  # For personalizing the user interface
    is_active = Column(Boolean, default=True)  # Control access within the app
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Authentication fields
    hashed_password = Column(String, nullable=True)  # Only for password-based users
    is_saml_user = Column(Boolean, default=False)  # Flag to distinguish authentication method
    
    # SAML-specific fields
    saml_subject_id = Column(String, nullable=True, unique=True)  # Critical permanent unique ID from objectidentifier claim
    azure_role = Column(String, nullable=True)  # Raw Azure role from role/rbac claim
    
    # Role mapping
    role_id = Column(Integer, ForeignKey("roles.id"))  # Internal role mapping
    role = relationship("Role", back_populates="users")
    
    # Relationship to audit logs
    audit_logs = relationship("AuditLog", back_populates="user")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    resource = Column(String, nullable=False)  # e.g., 'users', 'documents', 'system'
    action = Column(String, nullable=False)    # e.g., 'create', 'read', 'update', 'delete'
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    document_path = Column(String)  # Path to uploaded document
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
