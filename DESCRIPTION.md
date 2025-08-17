# HR Candidate Management System
[Demo Video](https://drive.google.com/file/d/1aLY33dbA2CT_DYXsIrYPsNcxbsN5OzSR/view?usp=drive_link)
A modern, role-based candidate management system with document upload capabilities and comprehensive permissions system.

## 🚀 Features

### Core Functionality
- **Role-Based Access Control**: Different permissions for Super Admin, HR Manager, Recruiter, HR Intern, and Hiring Manager
- **Document Management**: Upload and view candidate documents (PDFs, Word docs, etc.)
- **Simplified Candidate Profiles**: Focus on essential information (name, email, documents)
- **Audit Logging**: Track all user activities and changes
- **Modern UI**: Clean, responsive interface with modern design

### User Roles & Permissions

#### 🔐 Super Admin
- Full system access
- User management (create, update, delete users)
- Role and permission management
- System configuration
- Audit log access

#### 👩‍💼 HR Manager
- Full candidate management (create, read, update, delete)
- Document upload and viewing
- Export capabilities
- User management (limited)

#### 🤝 Recruiter
- Candidate management (create, read, update)
- Document upload and viewing
- Standard querying capabilities

#### 📝 HR Intern / Sourcer
- Limited candidate access (create, read with restrictions)
- Document upload only
- Basic search capabilities

#### 👨‍💼 Hiring Manager
- Read-only access to assigned candidates
- View documents for assigned candidates
- Add comments and ratings

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Login-Permissions
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\\Scripts\\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-super-secret-key-here
   DATABASE_URL=sqlite:///./app.db
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   APP_NAME=HR Candidate Management
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```
   or
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the application**
   Open your browser and go to: `http://localhost:8000`

### Default Login Credentials

After running `init_db.py`, you can log in with:

- **Super Admin**: `admin@example.com` / `admin123`
- **HR Manager**: `hr.manager@example.com` / `hrmanager123`
- **Recruiter**: `recruiter@example.com` / `recruiter123`

## 📁 Project Structure

```
Login-Permissions/
├── main.py                 # FastAPI application and routes
├── auth.py                 # Authentication and authorization logic
├── database.py             # Database models and connection
├── schemas.py              # Pydantic schemas for API validation
├── crud.py                 # Database operations
├── config.py              # Configuration settings
├── init_db.py             # Database initialization script
├── migrate_candidates.py   # Database migration script
├── requirements.txt        # Python dependencies
├── documents/             # Document storage directory
├── templates/             # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── candidates.html
│   └── user_management.html
└── __pycache__/           # Python cache files
```

## 🎯 Usage Guide

### For HR Managers

1. **Add New Candidates**
   - Navigate to Candidate Management
   - Fill in candidate name and email
   - Optionally upload a resume/document
   - Click "Add Candidate"

2. **View Documents**
   - Click "View Document" button on any candidate card
   - Documents are securely stored and served

3. **Manage Users**
   - Access User Management from the dashboard
   - Create new users with appropriate roles
   - Assign permissions based on organizational needs

### For Recruiters

1. **Upload Candidate Documents**
   - Use the drag-and-drop interface to upload resumes
   - Supported formats: PDF, DOC, DOCX, TXT

2. **Search and Filter**
   - Use the search functionality to find specific candidates
   - Filter by various criteria

### For HR Interns

1. **Basic Data Entry**
   - Add candidate information (limited fields)
   - Upload documents for processing
   - Cannot view sensitive information

## 🔧 Customization

### Adding New Roles

1. **Create Role in Database**
   ```python
   # In init_db.py or through the admin interface
   role = crud.create_role(db, schemas.RoleCreate(
       name="Custom Role",
       description="Description of the role"
   ))
   ```

2. **Assign Permissions**
   ```python
   # Assign specific permissions to the role
   permissions = ["candidates:read", "documents:view"]
   for perm_name in permissions:
       permission = crud.get_permission_by_name(db, perm_name)
       crud.assign_permission_to_role(db, role.id, permission.id)
   ```

### Modifying UI

- Templates are located in the `templates/` directory
- Modify HTML files to customize the interface
- CSS is embedded in the templates for easy customization

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt for secure password storage
- **Role-Based Access Control**: Granular permissions system
- **Audit Logging**: Complete activity tracking
- **File Upload Validation**: Secure document handling

## 📊 Monitoring and Logs

### Audit Logs
- All user activities are logged
- Includes user, action, resource, and timestamp
- Accessible through the dashboard for authorized users

### Health Check
- Endpoint: `GET /health`
- Returns system status and timestamp

## 🚀 Deployment

### Production Setup

1. **Environment Variables**
   ```env
   SECRET_KEY=production-secret-key
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ACCESS_TOKEN_EXPIRE_MINUTES=480
   APP_NAME=HR Management System
   ```

2. **Database Migration**
   - For PostgreSQL: Use `setup_postgres.py`
   - Run migration scripts before deployment

3. **WSGI Server**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support or questions:
- Check the documentation
- Review the code comments
- Create an issue in the repository

## 🔄 Version History

- **v1.0.0**: Initial release with basic RBAC
- **v1.1.0**: Added candidate management
- **v1.2.0**: Document upload functionality
- **v1.3.0**: Improved UI and simplified candidate fields

---

**Built with FastAPI, SQLAlchemy, and modern web technologies** 🚀