"""
Unit tests for the User model.

This module tests the user model's validation rules, including:
1. Base user validation (username, email)
2. User creation validation (password)
3. User update validation (optional fields)
4. Database model validation (password hash)
5. Response model validation (excluded fields)
"""
from typing import Optional

import pytest
from pydantic import ValidationError, EmailStr

from app.models.user import (
    UserBase, UserCreate, UserUpdate, UserInDB, UserResponse
)

pytestmark = pytest.mark.unit

def test_create_user_base_success(sample_user_data):
    """Test creating a base user with valid data."""
    user = UserBase(**sample_user_data)
    assert user.username == sample_user_data["username"]
    assert user.email == sample_user_data["email"]

def test_create_user_base_without_email():
    """Test creating a base user without email (optional field)."""
    data = {
        "username": "testuser"
    }
    user = UserBase(**data)
    assert user.username == "testuser"
    assert user.email is None

def test_create_user_base_invalid_email():
    """Test creating a base user with invalid email."""
    invalid_data = {
        "username": "testuser",
        "email": "invalid-email"  # Not a valid email format
    }
    with pytest.raises(ValidationError) as exc_info:
        UserBase(**invalid_data)
    assert "email" in str(exc_info.value)

def test_create_user_base_missing_username():
    """Test creating a base user without required username."""
    invalid_data = {
        "email": "test@example.com"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserBase(**invalid_data)
    assert "username" in str(exc_info.value)

def test_create_user_success(sample_user_data):
    """Test creating a new user with valid data."""
    create_data = {
        **sample_user_data,
        "password": "SecurePassword123"
    }
    user = UserCreate(**create_data)
    assert user.username == create_data["username"]
    assert user.email == create_data["email"]
    assert user.password == "SecurePassword123"

def test_create_user_missing_password():
    """Test creating a new user without required password."""
    data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)  # Missing password
    assert "password" in str(exc_info.value)

def test_update_user_empty():
    """Test creating an empty user update (all fields optional)."""
    update = UserUpdate()
    assert update.username is None
    assert update.email is None
    assert update.password is None

def test_update_user_partial():
    """Test partial user update."""
    update_data = {
        "username": "newusername"
    }
    update = UserUpdate(**update_data)
    assert update.username == "newusername"
    assert update.email is None
    assert update.password is None

def test_update_user_full():
    """Test full user update with all fields."""
    update_data = {
        "username": "newusername",
        "email": "new@example.com",
        "password": "newpassword123"
    }
    update = UserUpdate(**update_data)
    assert update.username == update_data["username"]
    assert update.email == update_data["email"]
    assert update.password == update_data["password"]

def test_update_user_invalid_email():
    """Test user update with invalid email."""
    invalid_data = {
        "email": "invalid-email"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(**invalid_data)
    assert "email" in str(exc_info.value)

def test_user_in_db(sample_user_data):
    """Test database user model with password hash."""
    db_data = {
        **sample_user_data,
        "password_hash": "hashed_password_string"
    }
    user = UserInDB(**db_data)
    assert user.username == db_data["username"]
    assert user.email == db_data["email"]
    assert user.password_hash == "hashed_password_string"

def test_user_in_db_missing_password_hash(sample_user_data):
    """Test database user model without required password hash."""
    with pytest.raises(ValidationError) as exc_info:
        UserInDB(**sample_user_data)  # Missing password_hash
    assert "password_hash" in str(exc_info.value)

def test_user_response(sample_user_data):
    """Test user response model excludes sensitive information."""
    user = UserResponse(**sample_user_data)
    assert user.username == sample_user_data["username"]
    assert user.email == sample_user_data["email"]
    
    # Verify sensitive fields are not included
    user_dict = user.model_dump()
    assert "password" not in user_dict
    assert "password_hash" not in user_dict

def test_email_str_validation():
    """Test that email validation uses EmailStr type."""
    # Verify the type hint is EmailStr
    assert UserBase.model_fields["email"].annotation == Optional[EmailStr]
    
    # Test with valid email
    user = UserBase(username="test", email="valid@example.com")
    assert isinstance(user.email, str)
    
    # Test with invalid email
    with pytest.raises(ValidationError):
        UserBase(username="test", email="invalid-email")
