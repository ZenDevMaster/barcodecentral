"""
Authentication module for Barcode Central
Handles user authentication and session management using Flask-Login
"""
import os
from flask_login import UserMixin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class User(UserMixin):
    """
    Simple User class for Flask-Login
    Since we only have one user (admin), we use a simple implementation
    """
    def __init__(self, user_id: str, username: str):
        self.id = user_id
        self.username = username

    def __repr__(self):
        return f'<User {self.username}>'


# Single admin user instance
ADMIN_USER = User(user_id='1', username=os.getenv('LOGIN_USER', 'admin'))


def load_user(user_id: str) -> User | None:
    """
    Flask-Login user_loader callback
    
    Args:
        user_id: The user ID to load
        
    Returns:
        User object if user_id is valid, None otherwise
    """
    if user_id == '1':
        return ADMIN_USER
    return None


def validate_credentials(username: str, password: str) -> bool:
    """
    Validate user credentials against environment variables
    
    Args:
        username: The username to validate
        password: The password to validate
        
    Returns:
        True if credentials are valid, False otherwise
    """
    expected_username = os.getenv('LOGIN_USER', 'admin')
    expected_password = os.getenv('LOGIN_PASSWORD', 'changeme')
    
    return username == expected_username and password == expected_password


def get_admin_user() -> User:
    """
    Get the admin user instance
    
    Returns:
        The admin User object
    """
    return ADMIN_USER


def get_current_username() -> str:
    """
    Get the current authenticated user's username
    
    Returns:
        Username string, or 'unknown' if not authenticated
    """
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return current_user.username
    except Exception:
        pass
    return 'unknown'