from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from config import settings
from database import get_db, engine, Base
import schemas
import crud
import auth
from auth import get_current_active_user, require_permission
from init_db import initialize_database

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive authentication and authorization system with role-based access control",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        initialize_database()
    except Exception as e:
        print(f"Database initialization error: {e}")

# Auth Routes
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Log the login
    crud.create_audit_log(db, user.id, "login", "authentication", f"User logged in from web interface")
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": settings.app_name,
        "error": error
    })

@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user = auth.authenticate_user(db, email, password)
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "app_name": settings.app_name,
                "error": "Invalid email or password"
            })
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = auth.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Log the login
        crud.create_audit_log(db, user.id, "login", "authentication", f"User logged in from web interface")
        
        # Redirect to dashboard with token in cookie
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response
        
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "app_name": settings.app_name,
            "error": "An error occurred during login"
        })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError()
        
        user = crud.get_user_by_email(db, email)
        if user is None:
            raise JWTError()
        
        # Get dashboard data
        dashboard_data = crud.get_user_dashboard_data(db, user.id)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "app_name": settings.app_name,
            "user": dashboard_data["user"],
            "permissions": dashboard_data["permissions"],
            "recent_activities": dashboard_data["recent_activities"]
        })
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)

@app.get("/user-management", response_class=HTMLResponse)
async def user_management_page(
    request: Request,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user has permission
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to manage users
        if not auth.check_permission(current_user, "users", "manage", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Get all users and roles
        users = crud.get_users(db)
        roles = crud.get_roles(db)
        
        return templates.TemplateResponse("user_management.html", {
            "request": request,
            "app_name": settings.app_name,
            "current_user": current_user,
            "users": users,
            "roles": roles,
            "success_message": success_message,
            "error_message": error_message
        })
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/dashboard?error=insufficient_permissions", status_code=302)

@app.post("/user-management", response_class=HTMLResponse)
async def create_user_form(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user has permission
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email_token: str = payload.get("sub")
        if email_token is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email_token)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to manage users
        if not auth.check_permission(current_user, "users", "manage", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Check if email already exists
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            users = crud.get_users(db)
            roles = crud.get_roles(db)
            return templates.TemplateResponse("user_management.html", {
                "request": request,
                "app_name": settings.app_name,
                "current_user": current_user,
                "users": users,
                "roles": roles,
                "error_message": f"A user with email '{email}' already exists."
            })
        
        # Create the user
        user_data = schemas.UserCreate(
            email=email,
            full_name=full_name,
            password=password,
            role_id=role_id
        )
        
        created_user = crud.create_user(db, user_data)
        
        # Log the action
        crud.create_audit_log(
            db, current_user.id, "create", "user", 
            f"Created user: {created_user.email} with role ID: {role_id}"
        )
        
        # Get updated users and roles
        users = crud.get_users(db)
        roles = crud.get_roles(db)
        
        return templates.TemplateResponse("user_management.html", {
            "request": request,
            "app_name": settings.app_name,
            "current_user": current_user,
            "users": users,
            "roles": roles,
            "success_message": f"User '{full_name}' has been created successfully!"
        })
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/dashboard?error=insufficient_permissions", status_code=302)
    except Exception as e:
        users = crud.get_users(db)
        roles = crud.get_roles(db)
        current_user = crud.get_user_by_email(db, email_token)
        return templates.TemplateResponse("user_management.html", {
            "request": request,
            "app_name": settings.app_name,
            "current_user": current_user,
            "users": users,
            "roles": roles,
            "error_message": f"An error occurred while creating the user: {str(e)}"
        })

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/api/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

@app.get("/api/users", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("users", "read"))
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.post("/api/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("users", "manage"))
):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = crud.create_user(db=db, user=user)
    
    # Log the action
    crud.create_audit_log(
        db, current_user.id, "create", "user", 
        f"Created user: {created_user.email}"
    )
    
    return created_user

@app.get("/api/roles", response_model=List[schemas.Role])
async def read_roles(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("roles", "read"))
):
    roles = crud.get_roles(db)
    return roles

@app.post("/api/roles", response_model=schemas.Role)
async def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("roles", "manage"))
):
    created_role = crud.create_role(db=db, role=role)
    
    # Log the action
    crud.create_audit_log(
        db, current_user.id, "create", "role", 
        f"Created role: {created_role.name}"
    )
    
    return created_role

@app.get("/api/permissions", response_model=List[schemas.Permission])
async def read_permissions(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    permissions = crud.get_permissions(db)
    return permissions

@app.post("/api/permissions", response_model=schemas.Permission)
async def create_permission(
    permission: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("system", "manage"))
):
    created_permission = crud.create_permission(db=db, permission=permission)
    
    # Log the action
    crud.create_audit_log(
        db, current_user.id, "create", "permission", 
        f"Created permission: {created_permission.name}"
    )
    
    return created_permission

@app.get("/api/audit-logs", response_model=List[schemas.AuditLog])
async def read_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(require_permission("audit", "read"))
):
    logs = crud.get_audit_logs(db, user_id=user_id, skip=skip, limit=limit)
    return logs

@app.get("/api/dashboard", response_model=schemas.UserDashboard)
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    dashboard_data = crud.get_user_dashboard_data(db, current_user.id)
    return dashboard_data

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
