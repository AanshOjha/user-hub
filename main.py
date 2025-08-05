from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager
from jose import jwt, JWTError
import os
import shutil

from config import settings
from database import get_db, engine, Base
import schemas
import crud
import auth
from auth import get_current_active_user
from init_db import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    try:
        initialize_database()
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield
    # Shutdown (if needed)

# Initialize the FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="HR Candidate Management System with role-based access control",
    version="2.0.0",
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()

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

# Candidate Management Web Routes
@app.get("/candidates", response_class=HTMLResponse)
async def candidates_page(
    request: Request,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to view candidates
        if not auth.check_permission(current_user, "candidates", "read", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Get all candidates
        candidates = crud.get_candidates(db)
        
        # Check permissions for UI controls
        can_create_candidates = auth.check_permission(current_user, "candidates", "create", db)
        can_delete_candidates = auth.check_permission(current_user, "candidates", "delete", db)
        can_manage_users = auth.check_permission(current_user, "users", "manage", db)
        
        return templates.TemplateResponse("candidates.html", {
            "request": request,
            "app_name": settings.app_name,
            "current_user": current_user,
            "candidates": candidates,
            "can_create_candidates": can_create_candidates,
            "can_delete_candidates": can_delete_candidates,
            "can_manage_users": can_manage_users,
            "success_message": success_message,
            "error_message": error_message
        })
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/dashboard?error=insufficient_permissions", status_code=302)

@app.post("/candidates/create")
async def create_candidate_web(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email_token: str = payload.get("sub")
        if email_token is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email_token)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to create candidates
        if not auth.check_permission(current_user, "candidates", "create", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Handle file upload
        document_path = None
        if document and document.filename:
            # Create documents directory if it doesn't exist
            os.makedirs("documents", exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(document.filename)[1]
            safe_filename = f"{timestamp}_{document.filename.replace(' ', '_')}"
            document_path = f"documents/{safe_filename}"
            
            # Save the file
            with open(document_path, "wb") as buffer:
                shutil.copyfileobj(document.file, buffer)
        
        # Create candidate
        candidate_data = schemas.CandidateCreate(
            name=name,
            email=email,
            document_path=document_path
        )
        
        new_candidate = crud.create_candidate(db, candidate_data, current_user.id)
        
        # Log the action
        crud.create_audit_log(
            db, 
            current_user.id, 
            "create", 
            "candidates", 
            f"Created candidate: {name}" + (f" with document: {document.filename}" if document else "")
        )
        
        return RedirectResponse(
            url=f"/candidates?success_message=Candidate '{name}' created successfully!",
            status_code=302
        )
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/candidates?error_message=Insufficient permissions", status_code=302)
    except Exception as e:
        return RedirectResponse(
            url=f"/candidates?error_message=Error creating candidate: {str(e)}",
            status_code=302
        )

@app.post("/candidates/delete/{candidate_id}")
async def delete_candidate_web(
    request: Request,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email_token: str = payload.get("sub")
        if email_token is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email_token)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to delete candidates
        if not auth.check_permission(current_user, "candidates", "delete", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Get candidate before deletion
        candidate = crud.get_candidate(db, candidate_id)
        if not candidate:
            return RedirectResponse(
                url="/candidates?error_message=Candidate not found",
                status_code=302
            )
        
        # Delete candidate
        crud.delete_candidate(db, candidate_id)
        
        # Log the action
        crud.create_audit_log(
            db,
            current_user.id,
            "delete",
            "candidates",
            f"Deleted candidate: {candidate.name}"
        )
        
        return RedirectResponse(
            url=f"/candidates?success_message=Candidate '{candidate.name}' deleted successfully!",
            status_code=302
        )
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/candidates?error_message=Insufficient permissions", status_code=302)
    except Exception as e:
        return RedirectResponse(
            url=f"/candidates?error_message=Error deleting candidate: {str(e)}",
            status_code=302
        )

@app.get("/candidates/{candidate_id}/document")
async def view_candidate_document(
    request: Request,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    # Get token from cookie and verify user
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token and get user

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError()
        
        current_user = crud.get_user_by_email(db, email)
        if current_user is None:
            raise JWTError()
        
        # Check if user has permission to view candidates
        if not auth.check_permission(current_user, "candidates", "read", db):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Get candidate
        candidate = crud.get_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        if not candidate.document_path or not os.path.exists(candidate.document_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Log the action
        crud.create_audit_log(
            db,
            current_user.id,
            "view",
            "documents",
            f"Viewed document for candidate: {candidate.name}"
        )
        
        return FileResponse(
            path=candidate.document_path,
            filename=os.path.basename(candidate.document_path),
            media_type='application/octet-stream'
        )
        
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)
    except HTTPException as e:
        return RedirectResponse(url=f"/candidates?error_message={e.detail}", status_code=302)
    except Exception as e:
        return RedirectResponse(
            url=f"/candidates?error_message=Error viewing document: {str(e)}",
            status_code=302
        )

# API Routes
@app.get("/")
async def root():
    """Redirect to login page"""
    return RedirectResponse(url="/login", status_code=302)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Essential API endpoints for dashboard data
@app.get("/api/dashboard", response_model=schemas.UserDashboard)
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get dashboard data for current user"""
    dashboard_data = crud.get_user_dashboard_data(db, current_user.id)
    return dashboard_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
