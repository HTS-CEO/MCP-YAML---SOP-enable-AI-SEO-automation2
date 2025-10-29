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
    """Separate admin login form"""
    if request.method == 'GET':
        return render_template('admin_login.html')

    # Get credentials from .env
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    username = request.form.get('username')
    password = request.form.get('password')

    if username == admin_username and password == admin_password:
        # Create admin session
        session['user_id'] = 'admin'
        session['username'] = admin_username
        session['role'] = 'admin'
        logger.info(f"Admin logged in: {admin_username}")
        return redirect(url_for('auth.admin_dashboard'))
    else:
        flash('Invalid admin credentials', 'error')
        return redirect(url_for('auth.admin_login'))

@auth_bp.route('/admin')
@admin_required
def admin_dashboard():
    try:
        users = user_manager.get_all_users()
        return render_template('admin_dashboard.html', users=users)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        # Return HTML error page instead of JSON for admin dashboard
        return render_template('error.html', error_message='An unexpected error occurred while loading the admin dashboard.'), 500

@auth_bp.route('/admin/users')
@admin_required
def admin_users():
    users = user_manager.get_all_users()
    return render_template('admin_users.html', users=users)

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
