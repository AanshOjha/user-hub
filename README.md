# Login Permissions System

A comprehensive FastAPI application with JWT-based authentication and role-based access control (RBAC) system.

## Features

- 🔐 **JWT Authentication**: Secure token-based authentication
- 👥 **Role-Based Access Control**: Comprehensive RBAC system with predefined roles
- 📊 **Dashboard**: User-friendly dashboard with permissions overview
- 🔍 **Audit Logging**: Track user activities and system events
- 🎨 **Modern UI**: Bootstrap-based responsive design
- 🛡️ **Security**: Password hashing, secure token handling
- 👨‍💼 **User Management**: Admin interface for creating users and assigning roles

## Roles & Permissions

### 🔐 Super Admin
- Full access to everything
- Can manage users, roles, system settings, audit logs

### 👩‍💼 HR Manager
- Full control over recruitment data
- Can manage all documents, view/edit/export data, run AI queries
- Cannot change system settings or higher roles

### 🤝 Recruiter
- Can upload/view/edit documents and run queries
- Cannot delete or export sensitive data

### 📝 HR Intern / Sourcer
- Can upload/view limited info
- Cannot edit/delete/see PII or use advanced AI features

### 👨‍💼 Hiring Manager
- Read-only access to assigned candidates
- Can comment/rate, but nothing else

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Login-Permissions
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env` file and update with your settings
   - Generate a secure SECRET_KEY for production

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:8000`

## Default Admin Account

- **Email**: admin@example.com
- **Password**: admin123

⚠️ **Important**: Change the default admin password in production!

## User Management

The application includes a comprehensive user management interface for system administrators:

### Features:
- **Create Users**: Add new users with email, password, and full name
- **Role Assignment**: Select from available roles via dropdown menu
- **User Overview**: View all existing users with their roles and status
- **Role Descriptions**: Clear descriptions of each role's permissions
- **Audit Trail**: All user creation actions are logged for security

### Access:
- Only users with "manage users" permission can access user management
- Available in the dashboard dropdown menu and quick actions
- Direct URL: `/user-management`

### Available Roles:
- **Super Admin**: Full system access
- **HR Manager**: Full recruitment data control
- **Recruiter**: Document management and AI queries
- **HR Intern/Sourcer**: Limited upload and view access
- **Hiring Manager**: Read-only access to assigned candidates

## API Endpoints

### Authentication
- `POST /token` - Get JWT token
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /logout` - Logout

### User Management
- `GET /user-management` - User management interface (admin only)
- `POST /user-management` - Create new user with role assignment (admin only)

### Users
- `GET /api/users/me` - Get current user info
- `GET /api/users` - List all users (requires permission)
- `POST /api/users` - Create new user (requires permission)

### Roles & Permissions
- `GET /api/roles` - List all roles
- `POST /api/roles` - Create new role (requires permission)
- `GET /api/permissions` - List all permissions
- `POST /api/permissions` - Create new permission (requires permission)

### Audit & Dashboard
- `GET /api/audit-logs` - View audit logs (requires permission)
- `GET /api/dashboard` - Get dashboard data
- `GET /dashboard` - Dashboard page

## Configuration

The application uses environment variables for configuration:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `APP_NAME` - Application name

## Database Schema

The application uses SQLAlchemy with the following models:

- **User**: User accounts with authentication
- **Role**: User roles for RBAC
- **Permission**: Granular permissions
- **RolePermission**: Many-to-many relationship between roles and permissions
- **AuditLog**: System activity tracking

## Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control
- Permission-based route protection
- Audit logging for security events
- Secure cookie handling

## Development

For development, you can run the application with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

1. Update environment variables for production
2. Use a production database (PostgreSQL recommended)
3. Set up proper SSL/TLS certificates
4. Configure reverse proxy (nginx recommended)
5. Use production WSGI server settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
