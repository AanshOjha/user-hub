"""
PostgreSQL Database Setup Script

This script helps you create the database and user for the Login Permissions System.
Run this after setting up PostgreSQL on your system.

Instructions:
1. Make sure PostgreSQL is installed and running
2. Update the .env file with your PostgreSQL credentials
3. Create the database manually or use this script as reference

SQL Commands to run in PostgreSQL:
"""

SETUP_SQL = """
-- Connect to PostgreSQL as superuser (usually postgres)
-- Create database
CREATE DATABASE login_permissions_db;

-- Create user (optional if you want a dedicated user)
CREATE USER login_user WITH PASSWORD 'your_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE login_permissions_db TO login_user;

-- Connect to the login_permissions_db database and grant schema privileges
\\c login_permissions_db
GRANT ALL ON SCHEMA public TO login_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO login_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO login_user;
"""

print("PostgreSQL Setup Instructions:")
print("=" * 50)
print(SETUP_SQL)
print("\nAfter setting up the database:")
print("1. Update the .env file with your database credentials")
print("2. Run: python init_db.py to initialize the database with default data")
print("3. Run: python run.py to start the application")
