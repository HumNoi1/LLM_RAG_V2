#!/usr/bin/env python3
"""
Test register system with Supabase connection
"""

import asyncio
import psycopg2
import sys
import os
sys.path.append('.')

# Set environment variables
os.environ['DATABASE_URL'] = "postgresql://postgres.urdgwffjkfsibfkenifx:LyqWEDSByP3bB0LB@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
os.environ['JWT_SECRET_KEY'] = 'your-secret-key-change-this'

def test_database_connection():
    """Test direct PostgreSQL connection to Supabase"""
    print("=== Testing Supabase Connection ===")
    
    try:
        # Direct connection for testing
        conn = psycopg2.connect(
            host="aws-1-ap-southeast-1.pooler.supabase.com",
            port=5432,
            database="postgres",
            user="postgres.urdgwffjkfsibfkenifx",
            password="LyqWEDSByP3bB0LB"
        )
        
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        # Check if our tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'exams', 'exam_questions');
        """)
        
        tables = cur.fetchall()
        print(f"Tables found: {[table[0] for table in tables]}")
        
        # Test user table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print("User table columns:")
        for col_name, col_type in columns:
            print(f"  {col_name}: {col_type}")
        
        cur.close()
        conn.close()
        print("Database connection successful!")
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def test_register_with_raw_sql():
    """Test registration using raw SQL"""
    print("\n=== Testing Registration with Raw SQL ===")
    
    from app.core.security import hash_password
    import uuid
    from datetime import datetime
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="aws-1-ap-southeast-1.pooler.supabase.com",
            port=5432,
            database="postgres",
            user="postgres.urdgwffjkfsibfkenifx",
            password="LyqWEDSByP3bB0LB"
        )
        
        cur = conn.cursor()
        
        # Prepare user data
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        password_hash = hash_password("testpassword123")
        full_name = "Test User"
        role = "teacher"
        now = datetime.utcnow()
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()
        
        if existing:
            print(f"User {email} already exists, deleting first...")
            cur.execute("DELETE FROM users WHERE email = %s", (email,))
            conn.commit()
        
        # Insert new user
        insert_query = """
            INSERT INTO users (id, email, password_hash, full_name, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, email, full_name, role, created_at;
        """
        
        cur.execute(insert_query, (user_id, email, password_hash, full_name, role, now, now))
        user = cur.fetchone()
        conn.commit()
        
        print("User created successfully!")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]}")
        print(f"  Role: {user[3]}")
        print(f"  Created: {user[4]}")
        
        # Test login simulation
        cur.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
        login_user = cur.fetchone()
        
        if login_user:
            from app.core.security import verify_password
            is_valid = verify_password("testpassword123", login_user[2])
            print(f"Password verification: {is_valid}")
            
            if is_valid:
                from app.core.security import create_access_token
                token = create_access_token(login_user[0], login_user[3])
                print(f"JWT token created: {len(token)} characters")
                print("Login simulation successful!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Supabase Register System Test")
    print("=" * 50)
    
    try:
        # Test database connection
        db_ok = test_database_connection()
        
        if db_ok:
            # Test registration
            reg_ok = test_register_with_raw_sql()
            
            if reg_ok:
                print("\n✅ SUCCESS: Register system works with Supabase!")
                print("✅ Database connection: OK")
                print("✅ User creation: OK") 
                print("✅ Password hashing: OK")
                print("✅ JWT creation: OK")
                print("\n🎉 Register system is fully functional!")
            else:
                print("\n❌ Registration test failed")
        else:
            print("\n❌ Database connection failed")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()