"""
Database Migration Script
This script adds user_id columns to existing tables for user isolation
Run this ONCE before using the updated application
"""

import sqlite3
import os


def migrate_database(db_path: str = "eduai_data.db"):
    """Add user_id columns to all tables"""
    
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found. No migration needed.")
        return
    
    print(f"Starting migration of {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_id column exists in conversations table
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to conversations table...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN user_id INTEGER")
            print("✓ conversations table updated")
        else:
            print("✓ conversations table already has user_id column")
        
        # Check and update app_state table
        cursor.execute("PRAGMA table_info(app_state)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to app_state table...")
            cursor.execute("ALTER TABLE app_state ADD COLUMN user_id INTEGER")
            print("✓ app_state table updated")
        else:
            print("✓ app_state table already has user_id column")
        
        # Check and update documents table
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to documents table...")
            cursor.execute("ALTER TABLE documents ADD COLUMN user_id INTEGER")
            print("✓ documents table updated")
        else:
            print("✓ documents table already has user_id column")
        
        # Check and update generated_content table
        cursor.execute("PRAGMA table_info(generated_content)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to generated_content table...")
            cursor.execute("ALTER TABLE generated_content ADD COLUMN user_id INTEGER")
            print("✓ generated_content table updated")
        else:
            print("✓ generated_content table already has user_id column")
        
        # Check and update sessions table
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER")
            print("✓ sessions table updated")
        else:
            print("✓ sessions table already has user_id column")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNOTE: All existing data will have user_id = NULL")
        print("This data will still be accessible but won't be user-specific")
        print("Consider deleting old test data if security is a concern")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()


def clean_old_data(db_path: str = "eduai_data.db"):
    """Optional: Delete all existing data (use with caution!)"""
    
    print("\n⚠️  WARNING: This will delete ALL existing data!")
    confirm = input("Type 'DELETE ALL DATA' to confirm: ")
    
    if confirm != "DELETE ALL DATA":
        print("Cancelled. No data was deleted.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM app_state")
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM generated_content")
        cursor.execute("DELETE FROM sessions")
        
        conn.commit()
        print("✅ All data deleted successfully")
        
    except Exception as e:
        print(f"❌ Error deleting data: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("EduAI Database Migration Script")
    print("=" * 60)
    print("\nThis script will add user_id columns to your database")
    print("to enable proper user isolation and security.\n")
    
    # Migrate the database
    migrate_database()
    
    # Ask if user wants to clean old data
    print("\n" + "=" * 60)
    print("Optional: Clean Old Data")
    print("=" * 60)
    clean_choice = input("\nDo you want to delete all existing data? (yes/no): ")
    
    if clean_choice.lower() in ['yes', 'y']:
        clean_old_data()
    else:
        print("Old data preserved. Note: This data won't be user-specific.")
    
    print("\n✅ Setup complete! You can now run your application.")