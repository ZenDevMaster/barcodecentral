"""
Authentication Blueprint
Handles user authentication (login/logout)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from auth import validate_credentials

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


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
            session['user'] = username
            session.permanent = remember  # Remember session if checkbox checked
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
def logout():
    """Logout user and redirect to login"""
    username = session.get('user', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))