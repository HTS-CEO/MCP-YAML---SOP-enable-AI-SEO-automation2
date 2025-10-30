from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.models import user_manager, session_manager
from app.utils.logger import get_logger
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)
logger = get_logger()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.admin_login'))

        # Check if it's admin session (from .env credentials)
        if session.get('role') == 'admin':
            return f(*args, **kwargs)

        # Check database user role
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('auth.dashboard'))

        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Handle both JSON and form data
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form
    except Exception as e:
        logger.error(f"Error parsing request data: {str(e)}")
        if request.is_json:
            return jsonify({'error': 'Invalid request format'}), 400
        flash('Invalid request format', 'error')
        return redirect(url_for('auth.login'))

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        if request.is_json:
            return jsonify({'error': 'Username and password required'}), 400
        flash('Username and password required', 'error')
        return redirect(url_for('auth.login'))

    result = user_manager.authenticate_user(username, password)

    if 'error' in result:
        if request.is_json:
            return jsonify({'error': result['error']}), 401
        flash(result['error'], 'error')
        return redirect(url_for('auth.login'))

    # If database is not configured, show a user-friendly message
    if result.get('error') == 'Database not configured':
        if request.is_json:
            return jsonify({'error': 'Login is currently unavailable. Please contact the administrator to set up the database.'}), 503
        flash('Login is currently unavailable. Please contact the administrator to set up the database.', 'error')
        return redirect(url_for('auth.login'))

    # Create session
    session_result = session_manager.create_session(
        result['user']['id'],
        request.remote_addr,
        request.headers.get('User-Agent', '')
    )

    if 'error' in session_result:
        if request.is_json:
            return jsonify({'error': 'Session creation failed'}), 500
        flash('Login failed', 'error')
        return redirect(url_for('auth.login'))

    # Set session
    session['user_id'] = result['user']['id']
    session['username'] = result['user']['username']
    session['role'] = result['user']['role']

    logger.info(f"User logged in: {result['user']['username']}")

    if request.is_json:
        return jsonify({
            'success': True,
            'user': result['user'],
            'token': session_result['token']
        })

    # Redirect based on role
    if result['user']['role'] == 'admin':
        return redirect(url_for('auth.admin_dashboard'))
    else:
        return redirect(url_for('auth.dashboard'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # Handle both JSON and form data
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form
    except Exception as e:
        logger.error(f"Error parsing request data: {str(e)}")
        if request.is_json:
            return jsonify({'error': 'Invalid request format'}), 400
        flash('Invalid request format', 'error')
        return redirect(url_for('auth.register'))

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([username, email, password, confirm_password]):
        if request.is_json:
            return jsonify({'error': 'All fields required'}), 400
        flash('All fields required', 'error')
        return redirect(url_for('auth.register'))

    if password != confirm_password:
        if request.is_json:
            return jsonify({'error': 'Passwords do not match'}), 400
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth.register'))

    if len(password) < 6:
        if request.is_json:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('auth.register'))

    result = user_manager.create_user(username, email, password)

    if 'error' in result:
        if request.is_json:
            return jsonify({'error': result['error']}), 400
        flash(result['error'], 'error')
        return redirect(url_for('auth.register'))

    # If database is not configured, show a user-friendly message
    if result.get('error') == 'Database not configured':
        if request.is_json:
            return jsonify({'error': 'Registration is currently unavailable. Please contact the administrator to set up the database.'}), 503
        flash('Registration is currently unavailable. Please contact the administrator to set up the database.', 'error')
        return redirect(url_for('auth.register'))

    if request.is_json:
        return jsonify({'success': True, 'message': 'User registered successfully'})

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = session.get('user_id')
    if user_id and user_id != 'admin':  # Don't try to destroy admin sessions in DB
        # Destroy session in database
        session_token = session.get('session_token')
        if session_token:
            session_manager.destroy_session(user_id, session_token)

    logger.info(f"User logged out: {session.get('username')}")

    # Clear Flask session
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    logger.info(f"Admin logged out: {session.get('username')}")
    session.clear()
    flash('Admin logged out successfully', 'success')
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user = user_manager.get_user_by_id(session['user_id'])
    return render_template('dashboard.html', user=user)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        user = user_manager.get_user_by_id(session['user_id'])
        return render_template('profile.html', user=user)

    # Handle profile updates
    data = request.get_json() or request.form
    updates = {}

    if 'email' in data and data['email']:
        updates['email'] = data['email']

    if updates:
        result = user_manager.update_user(session['user_id'], updates)
        if 'error' in result:
            if request.is_json:
                return jsonify({'error': result['error']}), 400
            flash(result['error'], 'error')
        else:
            if request.is_json:
                return jsonify({'success': True})
            flash('Profile updated successfully', 'success')

    return redirect(url_for('auth.profile'))

@auth_bp.route('/api-keys', methods=['GET', 'POST'])
@login_required
def api_keys():
    from app.models import api_key_manager

    if request.method == 'GET':
        try:
            user_keys = api_key_manager.get_user_api_keys(session['user_id'])
            return render_template('api_keys.html', api_keys=user_keys)
        except Exception as e:
            logger.error(f"Error fetching user API keys: {str(e)}")
            flash('Error loading API keys', 'error')
            return render_template('api_keys.html', api_keys=[])

    # Handle API key updates
    try:
        data = request.get_json() or request.form
        service_name = data.get('service_name')
        api_key = data.get('api_key')

        if not service_name or not api_key:
            if request.is_json:
                return jsonify({'error': 'Service name and API key required'}), 400
            flash('Service name and API key required', 'error')
            return redirect(url_for('auth.api_keys'))

        result = api_key_manager.set_user_api_key(session['user_id'], service_name, api_key)

        if 'error' in result:
            if request.is_json:
                return jsonify({'error': result['error']}), 400
            flash(result['error'], 'error')
        else:
            if request.is_json:
                return jsonify({'success': True})
            flash('API key updated successfully', 'success')
    except Exception as e:
        logger.error(f"Error updating API key: {str(e)}")
        if request.is_json:
            return jsonify({'error': 'An unexpected error occurred'}), 500
        flash('Error updating API key', 'error')

    return redirect(url_for('auth.api_keys'))

@auth_bp.route('/api-keys/<service_name>', methods=['DELETE'])
@login_required
def delete_api_key(service_name):
    """Delete a user's API key"""
    try:
        from app.models import api_key_manager

        # Check if the key exists and belongs to the user
        user_keys = api_key_manager.get_user_api_keys(session['user_id'])
        key_exists = any(key['service_name'] == service_name for key in user_keys)

        if not key_exists:
            return jsonify({'error': 'API key not found'}), 404

        # Delete the key (we'll need to add this method to the manager)
        result = api_key_manager.delete_user_api_key(session['user_id'], service_name)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({'success': True, 'message': 'API key deleted successfully'})

    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error deleting API key: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

# Admin Routes
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login form - authenticates against database"""
    if request.method == 'GET':
        return render_template('admin_login.html')

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('auth.admin_login'))

    result = user_manager.authenticate_user(username, password)

    if 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('auth.admin_login'))

    # Check if user has admin role
    if result['user']['role'] != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('auth.admin_login'))

    # Create session
    session_result = session_manager.create_session(
        result['user']['id'],
        request.remote_addr,
        request.headers.get('User-Agent', '')
    )

    if 'error' in session_result:
        flash('Login failed', 'error')
        return redirect(url_for('auth.admin_login'))

    # Set session
    session['user_id'] = result['user']['id']
    session['username'] = result['user']['username']
    session['role'] = result['user']['role']

    logger.info(f"Admin logged in: {result['user']['username']}")
    return redirect(url_for('auth.admin_dashboard'))

@auth_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        users = user_manager.get_all_users()
        return render_template('admin_dashboard.html', users=users)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        # Return proper admin dashboard with setup message
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Dashboard - SEO Automation System</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #f8fafc;
                    margin: 0;
                    padding: 40px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 20px;
                }}
                .setup-card {{
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .setup-icon {{
                    font-size: 48px;
                    color: #f59e0b;
                    margin-bottom: 20px;
                }}
                .setup-title {{
                    font-size: 24px;
                    color: #f59e0b;
                    margin-bottom: 15px;
                }}
                .setup-message {{
                    color: #94a3b8;
                    margin-bottom: 20px;
                    line-height: 1.6;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 25px;
                    text-align: center;
                    transition: all 0.3s ease;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
                }}
                .stat-icon {{
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 15px;
                    font-size: 20px;
                    color: white;
                }}
                .stat-value {{
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 5px;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .stat-label {{
                    color: #94a3b8;
                    font-size: 14px;
                }}
                .actions-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .action-card {{
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 25px;
                }}
                .action-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #6366f1;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .action-item {{
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 15px;
                    background: rgba(99, 102, 241, 0.1);
                    border-radius: 10px;
                    margin-bottom: 10px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    color: inherit;
                }}
                .action-item:hover {{
                    background: rgba(99, 102, 241, 0.2);
                    transform: translateX(5px);
                }}
                .action-icon {{
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #6366f1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 16px;
                }}
                .logout-btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    margin-top: 20px;
                }}
                .logout-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        <i class="fas fa-shield-alt"></i> Admin Panel
                    </div>
                    <h1>Admin Dashboard</h1>
                </div>

                <div class="setup-card">
                    <div class="setup-icon">
                        <i class="fas fa-cogs"></i>
                    </div>
                    <h2 class="setup-title">System Setup Required</h2>
                    <p class="setup-message">
                        The admin dashboard is currently unable to load because the database connection needs to be configured.
                        Please set up the DATABASE_URL environment variable to connect to your PostgreSQL database.
                    </p>
                    <p class="setup-message">
                        Once the database is configured, this dashboard will provide full administrative controls including user management,
                        system monitoring, and configuration options.
                    </p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="stat-value">0</div>
                        <div class="stat-label">Total Users</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-key"></i>
                        </div>
                        <div class="stat-value">0</div>
                        <div class="stat-label">Active API Keys</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="stat-value">0</div>
                        <div class="stat-label">Total Requests</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-server"></i>
                        </div>
                        <div class="stat-value">Setup</div>
                        <div class="stat-label">System Status</div>
                    </div>
                </div>

                <div class="actions-grid">
                    <div class="action-card">
                        <h3 class="action-title">
                            <i class="fas fa-cog"></i> System Configuration
                        </h3>
                        <a href="/admin/api-keys" class="action-item">
                            <div class="action-icon">
                                <i class="fas fa-key"></i>
                            </div>
                            <div>
                                <strong>Configure API Keys</strong>
                                <br><small>Set up system-wide API keys for external services</small>
                            </div>
                        </a>
                        <div class="action-item" style="cursor: not-allowed; opacity: 0.6;">
                            <div class="action-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div>
                                <strong>User Management</strong>
                                <br><small>Available after database setup</small>
                            </div>
                        </div>
                    </div>

                    <div class="action-card">
                        <h3 class="action-title">
                            <i class="fas fa-info-circle"></i> System Information
                        </h3>
                        <div class="action-item" style="cursor: default;">
                            <div class="action-icon">
                                <i class="fas fa-database"></i>
                            </div>
                            <div>
                                <strong>Database Status</strong>
                                <br><small>Not configured - setup required</small>
                            </div>
                        </div>
                        <div class="action-item" style="cursor: default;">
                            <div class="action-icon">
                                <i class="fas fa-play-circle"></i>
                            </div>
                            <div>
                                <strong>Background Tasks</strong>
                                <br><small>Waiting for database configuration</small>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="/admin/logout" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, 200

@auth_bp.route('/admin')
def admin_login_redirect():
    """Redirect /admin to /admin/login"""
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/admin/users')
@admin_required
def admin_users():
    try:
        users = user_manager.get_all_users()
        return render_template('admin_users.html', users=users)
    except Exception as e:
        logger.error(f"Error loading admin users page: {str(e)}")
        # Return simple HTML page for admin users page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Users - SEO Automation System</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #f8fafc;
                    margin: 0;
                    padding: 40px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 20px;
                }}
                .setup-card {{
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .setup-icon {{
                    font-size: 48px;
                    color: #f59e0b;
                    margin-bottom: 20px;
                }}
                .setup-title {{
                    font-size: 24px;
                    color: #f59e0b;
                    margin-bottom: 15px;
                }}
                .setup-message {{
                    color: #94a3b8;
                    margin-bottom: 20px;
                    line-height: 1.6;
                }}
                .nav-links {{
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                    margin-bottom: 30px;
                }}
                .nav-link {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    background: rgba(99, 102, 241, 0.1);
                    color: #6366f1;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }}
                .nav-link:hover {{
                    background: rgba(99, 102, 241, 0.2);
                    transform: translateY(-2px);
                }}
                .logout-btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    margin-top: 20px;
                }}
                .logout-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        <i class="fas fa-shield-alt"></i> Admin Panel
                    </div>
                    <h1>User Management</h1>
                </div>

                <div class="nav-links">
                    <a href="/admin/dashboard" class="nav-link">
                        <i class="fas fa-tachometer-alt"></i>
                        Dashboard
                    </a>
                    <a href="/admin/api-keys" class="nav-link">
                        <i class="fas fa-key"></i>
                        API Keys
                    </a>
                </div>

                <div class="setup-card">
                    <div class="setup-icon">
                        <i class="fas fa-database"></i>
                    </div>
                    <h2 class="setup-title">Database Not Configured</h2>
                    <p class="setup-message">
                        The DATABASE_URL environment variable is not set. Please configure your PostgreSQL database connection.
                    </p>
                    <p class="setup-message">
                        Create a .env file in your project root with: DATABASE_URL=postgresql://username:password@host:port/database
                    </p>
                    <p class="setup-message">
                        Once configured, you'll be able to manage users, view statistics, and perform all administrative functions.
                    </p>
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="/admin/logout" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, 200

@auth_bp.route('/admin/api-keys', methods=['GET'])
@admin_required
def admin_api_keys():
    # API keys are now managed exclusively through .env file
    # This endpoint now shows configuration information only
    return render_template('admin_api_keys.html')

# Removed: Global API key deletion endpoint - API keys now managed via .env only

@auth_bp.route('/admin/users', methods=['POST'])
@admin_required
def admin_create_user():
    """Create a new user (admin only)"""
    try:
        data = request.get_json() or request.form

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400

        result = user_manager.create_user(username, email, password, role)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({'success': True, 'user_id': result['user_id']})

    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@auth_bp.route('/admin/users/<int:user_id>', methods=['GET', 'POST', 'DELETE'])
@admin_required
def admin_user_detail(user_id):
    if request.method == 'GET':
        user = user_manager.get_user_by_id(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.admin_users'))
        return render_template('admin_user_detail.html', user=user)

    elif request.method == 'POST':
        # Update user
        data = request.get_json() or request.form
        updates = {}

        for field in ['username', 'email', 'role', 'is_active', 'subscription_plan']:
            if field in data:
                updates[field] = data[field]

        if updates:
            result = user_manager.update_user(user_id, updates)
            if 'error' in result:
                if request.is_json:
                    return jsonify({'error': result['error']}), 400
                flash(result['error'], 'error')
            else:
                if request.is_json:
                    return jsonify({'success': True})
                flash('User updated successfully', 'success')

    elif request.method == 'DELETE':
        # Check if user exists
        user = user_manager.get_user_by_id(user_id)
        if not user:
            if request.is_json:
                return jsonify({'error': 'User not found'}), 404
            flash('User not found', 'error')
            return redirect(url_for('auth.admin_users'))

        # Delete user
        result = user_manager.delete_user(user_id)
        if 'error' in result:
            if request.is_json:
                return jsonify({'error': result['error']}), 400
            flash(result['error'], 'error')
        else:
            if request.is_json:
                return jsonify({'success': True})
            flash('User deleted successfully', 'success')

    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    try:
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Toggle status
        new_status = not user['is_active']
        result = user_manager.update_user(user_id, {'is_active': new_status})

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({'success': True, 'new_status': new_status})

    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error toggling user status: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@auth_bp.route('/admin/backup', methods=['POST'])
@admin_required
def admin_backup_system():
    """Create system backup"""
    try:
        from app.services.report_service import ReportService
        import datetime
        from app.models import api_key_manager

        report_service = ReportService()

        # Create backup data
        backup_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'users': user_manager.get_all_users(),
            'global_api_keys': api_key_manager.get_global_api_keys(),
            'system_info': {
                'version': '1.0.0',
                'backup_type': 'full_system'
            }
        }

        # Save backup
        filename = report_service.create_backup(backup_data, 'admin_backup')

        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({'error': 'Failed to create backup'}), 500

@auth_bp.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
@admin_required
def api_get_user(user_id):
    """Get user details for admin"""
    if request.method == 'GET':
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    elif request.method == 'DELETE':
        # Delete user
        result = user_manager.delete_user(user_id)
        if 'error' in result:
            logger.error(f"Error deleting user: {result['error']}")
            return jsonify({'error': result['error']}), 400
        return jsonify({'success': True, 'message': 'User deleted successfully'})

# API Routes for AJAX calls
@auth_bp.route('/api/user')
@login_required
def api_user():
    user = user_manager.get_user_by_id(session['user_id'])
    return jsonify(user)

@auth_bp.route('/api/user/api-keys')
@login_required
def api_user_api_keys():
    try:
        from app.models import api_key_manager
        user_keys = api_key_manager.get_user_api_keys(session['user_id'])
        return jsonify(user_keys)
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error fetching user API keys: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@auth_bp.route('/api/users')
@admin_required
def api_users():
    users = user_manager.get_all_users()
    return jsonify(users)
