# HR Management System with SAML Authentication

A FastAPI-based HR management system with role-based access control and Azure AD SAML integration.

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Azure AD tenant (for SAML, optional)

### Installation
```bash
# 1. Clone and setup
git clone <repository-url>
cd Login-Permissions
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure database
createdb login_permissions_db
cp .env.example .env
# Edit .env with your database credentials

# 3. Run application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

Edit `.env`:
```env
# Database
DB_HOST=localhost
DB_NAME=login_permissions_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Admin account
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# SAML (Optional)
SAML_ENABLED=True
AZURE_TENANT_ID=your_tenant_id
AZURE_SAML_CERTIFICATE=your_certificate
```

## 🔐 User Roles

| Role | Permissions |
|------|-------------|
| Super Admin | Full system access |
| HR Manager | Full recruitment control |
| HR Intern | Limited access |
| Recruiter | Document management |
| Sourcer | Limited candidate access |
| Hiring Manager | Read-only access |

## 🌐 SAML Setup (Azure AD)

1. Create Enterprise Application in Azure AD
2. Configure SAML URLs:
   - Entity ID: `http://localhost:8000/auth/saml/metadata`
   - ACS URL: `http://localhost:8000/acs`
3. Add role claim: `http://schemas.microsoft.com/ws/2008/06/identity/claims/role`
4. Update `.env` with tenant ID and certificate

### Azure → Internal Role Mapping
- `hr-manager` → HR Manager
- `hr-intern` → HR Intern  
- `super-admin` → Super Admin
- `recruiter` → Recruiter
- `sourcer` → Sourcer
- `hiring-manager` → Hiring Manager

## 📁 Project Structure
```
├── main.py          # FastAPI routes
├── database.py      # Database models
├── crud.py         # Database operations
├── auth.py         # Authentication
├── saml_auth.py    # SAML integration
├── config.py       # Settings
└── templates/      # HTML templates
```

## 🚀 Access
- App: http://localhost:8000
- Admin: admin@example.com / admin123
- SAML users: Auto-created on login

## 🔗 Key Endpoints
- `/login` - Login page (local + SAML)
- `/auth/saml/login` - SAML login
- `/dashboard` - User dashboard
- `/user-management` - Admin panel
- `/candidates` - Candidate management
