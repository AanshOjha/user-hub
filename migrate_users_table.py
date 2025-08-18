"""
Migration script to update users table for optimized SAML and normal user support.

This script:
1. Removes unnecessary fields (updated_at, saml_session_index)
2. Makes saml_subject_id unique
3. Ensures proper indexes are in place

Run this after updating the database models.
"""

from sqlalchemy import text
from database import engine, get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_users_table():
    """Migrate the users table to the new optimized structure"""
    
    with engine.connect() as connection:
        try:
            # Start transaction
            trans = connection.begin()
            
            logger.info("Starting users table migration...")
            
            # Check if columns exist before dropping them
            try:
                # Check if updated_at column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'updated_at'
                """))
                
                if result.fetchone():
                    logger.info("Dropping updated_at column...")
                    connection.execute(text("ALTER TABLE users DROP COLUMN updated_at"))
                else:
                    logger.info("updated_at column does not exist, skipping...")
                    
            except Exception as e:
                logger.warning(f"Could not drop updated_at column: {e}")
            
            try:
                # Check if saml_session_index column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'saml_session_index'
                """))
                
                if result.fetchone():
                    logger.info("Dropping saml_session_index column...")
                    connection.execute(text("ALTER TABLE users DROP COLUMN saml_session_index"))
                else:
                    logger.info("saml_session_index column does not exist, skipping...")
                    
            except Exception as e:
                logger.warning(f"Could not drop saml_session_index column: {e}")
            
            # Add unique constraint to saml_subject_id if it doesn't exist
            try:
                logger.info("Adding unique constraint to saml_subject_id...")
                # First, clean up any duplicate saml_subject_id values
                connection.execute(text("""
                    UPDATE users 
                    SET saml_subject_id = NULL 
                    WHERE saml_subject_id IN (
                        SELECT saml_subject_id 
                        FROM (
                            SELECT saml_subject_id, COUNT(*) as cnt
                            FROM users 
                            WHERE saml_subject_id IS NOT NULL
                            GROUP BY saml_subject_id 
                            HAVING COUNT(*) > 1
                        ) AS duplicates
                    )
                """))
                
                # Add unique constraint
                connection.execute(text("ALTER TABLE users ADD CONSTRAINT uq_users_saml_subject_id UNIQUE (saml_subject_id)"))
                
            except Exception as e:
                logger.warning(f"Could not add unique constraint to saml_subject_id: {e}")
            
            # Ensure proper defaults are set
            try:
                logger.info("Setting proper defaults for existing records...")
                # Set is_saml_user to False for users without saml_subject_id
                connection.execute(text("""
                    UPDATE users 
                    SET is_saml_user = FALSE 
                    WHERE saml_subject_id IS NULL AND is_saml_user IS NULL
                """))
                
                # Set is_saml_user to True for users with saml_subject_id
                connection.execute(text("""
                    UPDATE users 
                    SET is_saml_user = TRUE 
                    WHERE saml_subject_id IS NOT NULL
                """))
                
            except Exception as e:
                logger.warning(f"Could not update default values: {e}")
            
            # Commit the transaction
            trans.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            logger.error(f"Migration failed: {e}")
            raise

def verify_migration():
    """Verify that the migration was successful"""
    
    with engine.connect() as connection:
        try:
            # Check table structure
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            logger.info("Current users table structure:")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Check constraints
            result = connection.execute(text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'users'
            """))
            
            constraints = result.fetchall()
            logger.info("Current constraints:")
            for constraint in constraints:
                logger.info(f"  {constraint[0]}: {constraint[1]}")
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")

if __name__ == "__main__":
    print("Starting database migration for optimized SAML/normal user support...")
    print("This will:")
    print("1. Remove unnecessary columns (updated_at, saml_session_index)")
    print("2. Add unique constraint to saml_subject_id")
    print("3. Set proper defaults for existing records")
    print()
    
    confirm = input("Do you want to proceed? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        try:
            migrate_users_table()
            print("\nVerifying migration...")
            verify_migration()
            print("\nMigration completed successfully!")
        except Exception as e:
            print(f"\nMigration failed: {e}")
            print("Please check the logs and resolve any issues before proceeding.")
    else:
        print("Migration cancelled.")
