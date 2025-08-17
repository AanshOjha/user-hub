#!/usr/bin/env python3
"""
Test script to validate environment variable configuration
"""
import os
import sys

def test_env_config():
    """Test that all environment variables are properly loaded"""
    try:
        from config import settings
        
        print("✅ Testing Environment Variable Configuration")
        print("=" * 50)
        
        # Test database configuration
        print(f"Database Host: {settings.db_host}")
        print(f"Database Port: {settings.db_port}")
        print(f"Database Name: {settings.db_name}")
        print(f"Database User: {settings.db_user}")
        print(f"Database Password: {'*' * len(settings.db_password)}")
        print(f"Database URL: {settings.database_url[:20]}...")
        
        # Test security configuration
        print(f"\nSecurity Configuration:")
        print(f"Secret Key: {'*' * len(settings.secret_key)} (length: {len(settings.secret_key)})")
        print(f"Algorithm: {settings.algorithm}")
        print(f"Token Expire Minutes: {settings.access_token_expire_minutes}")
        print(f"BCrypt Rounds: {settings.bcrypt_rounds}")
        
        # Test admin configuration
        print(f"\nAdmin Configuration:")
        print(f"Admin Email: {settings.admin_email}")
        print(f"Admin Password: {'*' * len(settings.admin_password)}")
        
        # Test application configuration
        print(f"\nApplication Configuration:")
        print(f"App Name: {settings.app_name}")
        print(f"Debug Mode: {settings.debug}")
        print(f"CORS Origins: {settings.cors_origins_list}")
        
        # Test additional security settings
        print(f"\nAdditional Security Settings:")
        print(f"Max Login Attempts: {settings.max_login_attempts}")
        print(f"Login Lockout Duration: {settings.login_lockout_duration}s")
        print(f"Session Timeout: {settings.session_timeout}s")
        
        # Validate critical settings
        errors = []
        
        if len(settings.secret_key) < 32:
            errors.append("❌ SECRET_KEY should be at least 32 characters long")
        else:
            print("✅ SECRET_KEY length is adequate")
            
        if settings.secret_key == "your-super-secret-key-change-this-in-production":
            errors.append("❌ SECRET_KEY is still using default value - CHANGE IT!")
        else:
            print("✅ SECRET_KEY has been changed from default")
            
        if settings.admin_password == "admin123":
            errors.append("⚠️  ADMIN_PASSWORD is still using default value - should be changed")
        else:
            print("✅ ADMIN_PASSWORD has been changed from default")
            
        if settings.debug and os.getenv("ENVIRONMENT") == "production":
            errors.append("⚠️  DEBUG mode is enabled in production")
        elif not settings.debug:
            print("✅ DEBUG mode is disabled")
            
        if errors:
            print("\n" + "=" * 50)
            print("SECURITY WARNINGS:")
            for error in errors:
                print(error)
        else:
            print("\n✅ All security checks passed!")
            
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

if __name__ == "__main__":
    success = test_env_config()
    sys.exit(0 if success else 1)
