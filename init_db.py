from sqlalchemy.orm import Session
from database import get_db, Role, Permission
import crud
import schemas

def init_roles_and_permissions(db: Session):
    """Initialize default roles and permissions"""
    
    # Define permissions
    permissions_data = [
        # User management
        {"name": "manage_users", "description": "Create, update, delete users", "resource": "users", "action": "manage"},
        {"name": "view_users", "description": "View user information", "resource": "users", "action": "read"},
        
        # Role management
        {"name": "manage_roles", "description": "Create, update, delete roles", "resource": "roles", "action": "manage"},
        {"name": "view_roles", "description": "View roles", "resource": "roles", "action": "read"},
        
        # System settings
        {"name": "manage_system", "description": "Manage system settings", "resource": "system", "action": "manage"},
        {"name": "view_system", "description": "View system settings", "resource": "system", "action": "read"},
        
        # Documents
        {"name": "manage_documents", "description": "Full document management", "resource": "documents", "action": "manage"},
        {"name": "upload_documents", "description": "Upload documents", "resource": "documents", "action": "create"},
        {"name": "view_documents", "description": "View documents", "resource": "documents", "action": "read"},
        {"name": "edit_documents", "description": "Edit documents", "resource": "documents", "action": "update"},
        {"name": "delete_documents", "description": "Delete documents", "resource": "documents", "action": "delete"},
        {"name": "export_data", "description": "Export data", "resource": "documents", "action": "export"},
        
        # Candidates
        {"name": "create_candidates", "description": "Create new candidates", "resource": "candidates", "action": "create"},
        {"name": "view_candidates", "description": "View candidate information", "resource": "candidates", "action": "read"},
        {"name": "update_candidates", "description": "Update candidate information", "resource": "candidates", "action": "update"},
        {"name": "delete_candidates", "description": "Delete candidates", "resource": "candidates", "action": "delete"},
        
        # AI Queries
        {"name": "run_ai_queries", "description": "Run AI queries", "resource": "ai", "action": "execute"},
        {"name": "advanced_ai", "description": "Use advanced AI features", "resource": "ai", "action": "advanced"},
        
        # Audit logs
        {"name": "view_audit_logs", "description": "View audit logs", "resource": "audit", "action": "read"},
        
        # Comments and ratings
        {"name": "comment_rate", "description": "Comment and rate candidates", "resource": "candidates", "action": "comment"},
        {"name": "view_assigned_candidates", "description": "View assigned candidates", "resource": "candidates", "action": "read_assigned"},
        
        # PII access
        {"name": "view_pii", "description": "View personally identifiable information", "resource": "pii", "action": "read"},
    ]
    
    # Create permissions
    created_permissions = {}
    for perm_data in permissions_data:
        existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_perm:
            permission = crud.create_permission(db, schemas.PermissionCreate(**perm_data))
            created_permissions[perm_data["name"]] = permission
        else:
            created_permissions[perm_data["name"]] = existing_perm
    
    # Define roles and their permissions
    roles_data = [
        {
            "name": "Super Admin",
            "description": "Full access to everything",
            "permissions": [
                "manage_users", "view_users", "manage_roles", "view_roles",
                "manage_system", "view_system", "manage_documents", "upload_documents",
                "view_documents", "edit_documents", "delete_documents", "export_data",
                "create_candidates", "view_candidates", "update_candidates", "delete_candidates",
                "run_ai_queries", "advanced_ai", "view_audit_logs", "comment_rate",
                "view_assigned_candidates", "view_pii"
            ]
        },
        {
            "name": "HR Manager",
            "description": "Full control over recruitment data, can't change system settings",
            "permissions": [
                "view_users", "manage_documents", "upload_documents", "view_documents",
                "edit_documents", "delete_documents", "export_data",
                "create_candidates", "view_candidates", "update_candidates", "delete_candidates",
                "run_ai_queries", "advanced_ai", "comment_rate", "view_assigned_candidates", "view_pii"
            ]
        },
        {
            "name": "Recruiter",
            "description": "Can upload/view/edit documents and run queries",
            "permissions": [
                "upload_documents", "view_documents", "edit_documents",
                "create_candidates", "view_candidates", "update_candidates",
                "run_ai_queries", "comment_rate", "view_assigned_candidates", "view_pii"
            ]
        },
        {
            "name": "HR Intern",
            "description": "Can upload/view limited info, no PII or advanced features",
            "permissions": [
                "upload_documents", "view_documents",
                "create_candidates", "view_candidates",
                "comment_rate"
            ]
        },
        {
            "name": "Sourcer",
            "description": "Can upload/view limited info, no PII or advanced features",
            "permissions": [
                "upload_documents", "view_documents",
                "create_candidates", "view_candidates",
                "comment_rate"
            ]
        },
        {
            "name": "Hiring Manager",
            "description": "Read-only access to assigned candidates",
            "permissions": [
                "view_assigned_candidates", "comment_rate"
            ]
        }
    ]
    
    # Create roles and assign permissions
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = crud.create_role(db, schemas.RoleCreate(
                name=role_data["name"],
                description=role_data["description"]
            ))
        else:
            role = existing_role
        
        # Assign permissions to role
        for perm_name in role_data["permissions"]:
            if perm_name in created_permissions:
                crud.assign_permission_to_role(db, role.id, created_permissions[perm_name].id)

def create_default_admin_user(db: Session):
    """Create a default admin user"""
    from config import settings
    
    existing_admin = crud.get_user_by_email(db, settings.admin_email)
    
    if not existing_admin:
        # Get Super Admin role
        super_admin_role = db.query(Role).filter(Role.name == "Super Admin").first()
        
        if super_admin_role:
            admin_user = crud.create_user(db, schemas.UserCreate(
                email=settings.admin_email,
                password=settings.admin_password,
                full_name="System Administrator",
                role_id=super_admin_role.id
            ))
            print(f"Created default admin user: {settings.admin_email}")
            print("⚠️  Check .env file for admin password")
            return admin_user
    
    return existing_admin

def initialize_database():
    """Initialize database with roles, permissions, and default admin user"""
    db = next(get_db())
    try:
        print("Initializing roles and permissions...")
        init_roles_and_permissions(db)
        
        print("Creating default admin user...")
        create_default_admin_user(db)
        
        print("Database initialization complete!")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()
