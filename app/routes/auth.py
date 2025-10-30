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
            return jsonify({'error': 'Login is currently unavailable. Please check database configuration.'}), 503
        flash('Login is currently unavailable. Please check database configuration.', 'error')
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

    # All users go to the same dashboard
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
            return jsonify({'error': 'Registration is currently unavailable. Please check database configuration.'}), 503
        flash('Registration is currently unavailable. Please check database configuration.', 'error')
        return redirect(url_for('auth.register'))

    if request.is_json:
        return jsonify({'success': True, 'message': 'User registered successfully'})

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = session.get('user_id')
    if user_id:
        # Destroy session in database
        session_token = session.get('session_token')
        if session_token:
            session_manager.destroy_session(user_id, session_token)

    logger.info(f"User logged out: {session.get('username')}")

    # Clear Flask session
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))


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
