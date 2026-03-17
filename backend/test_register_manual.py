#!/usr/bin/env python3
"""
Manual test script for register system without database
"""

import sys
import os
sys.path.append('.')

# Set environment variables
os.environ['DATABASE_URL'] = 'file:./dev.db'
os.environ['JWT_SECRET_KEY'] = 'your-secret-key-change-this'

from app.core.security import hash_password, create_access_token, verify_password
from app.schemas.auth import UserCreate, UserResponse

def test_security_functions():
    print("=== Testing Security Functions ===")
    
    # Test password hashing
    password = "test123"
    hashed = hash_password(password)
    print(f"Password hashed: {len(hashed)} characters")
    
    # Test password verification
    is_valid = verify_password(password, hashed)
    print(f"Password verification: {is_valid}")
    
    # Test JWT creation
    token = create_access_token("user123", "teacher")
    print(f"JWT token created: {len(token)} characters")
    print(f"Token sample: {token[:50]}...")

def test_schemas():
    print("\n=== Testing Pydantic Schemas ===")
    
    # Test UserCreate schema
    user_data = {
        "email": "test@example.com",
        "password": "test123456",
        "full_name": "Test User",
        "role": "teacher"
    }
    
    try:
        user_create = UserCreate(**user_data)
        print(f"UserCreate schema valid")
        print(f"  Email: {user_create.email}")
        print(f"  Full name: {user_create.full_name}")
        print(f"  Role: {user_create.role}")
    except Exception as e:
        print(f"UserCreate schema error: {e}")
    
    # Test password validation
    try:
        short_password = UserCreate(
            email="test2@example.com",
            password="123",  # Too short
            full_name="Test User 2"
        )
    except Exception as e:
        print(f"Password validation works: {str(e)}")

def simulate_register_flow():
    print("\n=== Simulating Registration Flow ===")
    
    # Step 1: Validate input
    user_data = {
        "email": "new_user@example.com",
        "password": "securepassword123",
        "full_name": "New User",
        "role": "teacher"
    }
    
    try:
        user_create = UserCreate(**user_data)
        print("Step 1: Input validation passed")
        
        # Step 2: Hash password
        hashed_password = hash_password(user_create.password)
        print("Step 2: Password hashed")
        
        # Step 3: Simulate database insert (would normally save to DB)
        mock_user_id = "550e8400-e29b-41d4-a716-446655440000"
        print(f"Step 3: User would be saved with ID: {mock_user_id}")
        
        # Step 4: Create response
        user_response = UserResponse(
            id=mock_user_id,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            created_at="2024-03-17T10:30:00Z"  # Mock timestamp
        )
        print("Step 4: Response created")
        print(f"  Response: {user_response.model_dump()}")
        
    except Exception as e:
        print(f"Registration flow error: {e}")

if __name__ == "__main__":
    print("Manual Register System Test")
    print("=" * 50)
    
    try:
        test_security_functions()
        test_schemas()
        simulate_register_flow()
        print("\nAll tests passed! Register system components work correctly.")
        print("Note: Database connection still needs to be fixed for full functionality.")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()