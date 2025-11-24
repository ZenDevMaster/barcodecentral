"""
Authentication Blueprint
Handles user authentication (login/logout)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from functools import wraps
from auth import validate_credentials, get_admin_user

auth_bp = Blueprint('auth', __name__)


# Note: We now use Flask-Login's login_required decorator imported above
# The custom decorator is no longer needed


@auth_bp.route('/')
def index():
    """Root route - redirect to dashboard if authenticated, else login"""
    if 'user' in session:
        return redirect(url_for('web.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login page and process login"""
    # If already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('web.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        
        if validate_credentials(username, password):
            # Get the admin user and login with Flask-Login
            user = get_admin_user()
            login_user(user, remember=remember)
            
            # Also set session for backward compatibility
            session['user'] = username
            session.permanent = remember
            flash(f'Welcome back, {username}!', 'success')
            
            # Redirect to next page if specified, otherwise dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('web.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user and redirect to login"""
    username = session.get('user', 'User')
    logout_user()  # Flask-Login logout
    session.clear()  # Clear session
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))