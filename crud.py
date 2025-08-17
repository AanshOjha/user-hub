from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import User, Role, Permission, RolePermission, AuditLog, Candidate
import schemas
from auth import get_password_hash
from datetime import datetime

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# Role CRUD
def create_role(db: Session, role: schemas.RoleCreate):
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_roles(db: Session):
    return db.query(Role).all()

def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

# Permission CRUD
def create_permission(db: Session, permission: schemas.PermissionCreate):
    db_permission = Permission(
        name=permission.name,
        description=permission.description,
        resource=permission.resource,
        action=permission.action
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permissions(db: Session):
    return db.query(Permission).all()

def assign_permission_to_role(db: Session, role_id: int, permission_id: int):
    # Check if permission is already assigned
    existing = db.query(RolePermission).filter(
        and_(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
    ).first()
    
    if not existing:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission
    return existing

def get_user_permissions(db: Session, user_id: int):
    """Get all permissions for a user through their role"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.role:
        return []
    
    permissions = []
    for role_perm in user.role.role_permissions:
        permissions.append(role_perm.permission)
    return permissions

# Audit Log CRUD
def create_audit_log(db: Session, user_id: int, action: str, resource: str, details: str = None):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log

def get_audit_logs(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def get_user_dashboard_data(db: Session, user_id: int):
    """Get dashboard data for a user"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    permissions = get_user_permissions(db, user_id)
    permission_names = [f"{p.resource}:{p.action}" for p in permissions]
    recent_activities = get_audit_logs(db, user_id=user_id, limit=10)
    
    return {
        "user": user,
        "permissions": permission_names,
        "recent_activities": recent_activities
    }

# Candidate CRUD
def create_candidate(db: Session, candidate: schemas.CandidateCreate, created_by: int):
    db_candidate = Candidate(
        name=candidate.name,
        email=candidate.email,
        document_path=candidate.document_path,
        created_by=created_by
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_candidate(db: Session, candidate_id: int):
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()

def get_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Candidate).offset(skip).limit(limit).all()

def update_candidate(db: Session, candidate_id: int, candidate_update: schemas.CandidateUpdate):
    db_candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if db_candidate:
        update_data = candidate_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_candidate, key, value)
        db.commit()
        db.refresh(db_candidate)
    return db_candidate

def delete_candidate(db: Session, candidate_id: int):
    db_candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if db_candidate:
        db.delete(db_candidate)
        db.commit()
    return db_candidate

# SAML User Management
def create_or_update_saml_user(db: Session, user_data: dict):
    """Create or update user from SAML authentication"""
    email = user_data.get('email')
    if not email:
        raise ValueError("Email is required for SAML user creation")
    
    # Check if user already exists
    db_user = get_user_by_email(db, email)
    
    # Map Azure role to internal role - Updated mapping based on your Azure AD roles
    azure_role = user_data.get('role', '').lower()
    role_mapping = {
        # Azure AD Role -> Internal Role Name (exact match to database)
        'hr-manager': 'HR Manager',
        'hiring-manager': 'Hiring Manager',
        'hr-intern': 'HR Intern',
        'recruiter': 'Recruiter',
        'super-admin': 'Super Admin',
        'sourcer': 'Sourcer'
    }
    
    internal_role_name = role_mapping.get(azure_role, 'HR Intern')  # Default to HR Intern
    role = get_role_by_name(db, internal_role_name)
    
    # If the mapped role doesn't exist, fallback to HR Intern
    if not role:
        print(f"Warning: Role '{internal_role_name}' not found for Azure role '{azure_role}', using HR Intern")
        role = get_role_by_name(db, 'HR Intern')
        
        # If HR Intern doesn't exist either, log error
        if not role:
            print(f"Error: Default role 'HR Intern' not found in database!")
            return None
    
    if db_user:
        # Update existing user
        db_user.full_name = user_data.get('name', db_user.full_name)
        db_user.is_saml_user = True
        db_user.saml_subject_id = user_data.get('nameid')
        db_user.saml_session_index = user_data.get('session_index')
        db_user.azure_role = user_data.get('role')
        if role:
            db_user.role_id = role.id
        db_user.is_active = True
        db.commit()
        db.refresh(db_user)
        
        # Log role assignment
        print(f"Updated SAML user {email} with Azure role '{azure_role}' -> Internal role '{internal_role_name}'")
    else:
        # Create new user
        db_user = User(
            email=email,
            full_name=user_data.get('name', email.split('@')[0]),
            is_saml_user=True,
            saml_subject_id=user_data.get('nameid'),
            saml_session_index=user_data.get('session_index'),
            azure_role=user_data.get('role'),
            role_id=role.id if role else None,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Log role assignment
        print(f"Created SAML user {email} with Azure role '{azure_role}' -> Internal role '{internal_role_name}'")
    
    return db_user

def get_role_by_name(db: Session, role_name: str):
    """Get role by name"""
    return db.query(Role).filter(Role.name == role_name).first()
