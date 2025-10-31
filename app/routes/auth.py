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

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    from app.models import user_settings_manager

    if request.method == 'GET':
        try:
            user_settings = user_settings_manager.get_user_settings(session['user_id'])
            return render_template('settings.html', settings=user_settings)
        except Exception as e:
            logger.error(f"Error fetching user settings: {str(e)}")
            flash('Error loading settings', 'error')
            return render_template('settings.html', settings={})

    # Handle settings updates
    try:
        data = request.get_json() or request.form
        settings_to_update = {}

        # Process API configuration settings
        api_settings = ['openai_api_key', 'semrush_api_key', 'wordpress_url', 'wordpress_username', 'wordpress_app_password', 'ga4_property_id']
        for setting in api_settings:
            if setting in data and data[setting]:
                settings_to_update[setting] = data[setting]

        # Process automation settings
        automation_settings = ['daily_ranking_check', 'weekly_gbp_posts', 'monthly_reports', 'auto_reoptimize_threshold', 'slack_notifications']
        for setting in automation_settings:
            if setting in data:
                settings_to_update[setting] = 'true' if data[setting] in ['true', 'on', '1'] else 'false'

        # Process notification settings
        notification_settings = ['slack_webhook_url', 'email_notifications', 'notify_blog_generation', 'notify_ranking_changes', 'notify_gbp_posts', 'notify_system_errors']
        for setting in notification_settings:
            if setting in data:
                if setting == 'slack_webhook_url':
                    settings_to_update[setting] = data[setting] or ''
                else:
                    settings_to_update[setting] = 'true' if data[setting] in ['true', 'on', '1'] else 'false'

        # Process system settings
        system_settings = ['database_backup', 'log_retention_days', 'api_rate_limit', 'debug_mode']
        for setting in system_settings:
            if setting in data:
                settings_to_update[setting] = data[setting]

        if settings_to_update:
            result = user_settings_manager.update_user_settings_bulk(session['user_id'], settings_to_update)
            if 'error' in result:
                if request.is_json:
                    return jsonify({'error': result['error']}), 400
                flash(result['error'], 'error')
            else:
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Settings saved successfully'})
                flash('Settings saved successfully', 'success')
        else:
            if request.is_json:
                return jsonify({'success': True, 'message': 'No settings to update'})
            flash('No settings to update', 'info')

    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        if request.is_json:
            return jsonify({'error': 'An unexpected error occurred'}), 500
        flash('Error updating settings', 'error')

    return redirect(url_for('auth.settings'))

@auth_bp.route('/api/settings')
@login_required
def api_get_settings():
    """Get user settings for AJAX calls"""
    try:
        from app.models import user_settings_manager
        user_settings = user_settings_manager.get_user_settings(session['user_id'])
        return jsonify(user_settings)
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error fetching user settings: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@auth_bp.route('/api/check_api_status')
@login_required
def check_api_status():
    """Check real-time status of user's API connections"""
    try:
        from app.models import api_key_manager
        user_id = session['user_id']

        # Get user's API keys
        user_keys = api_key_manager.get_user_api_keys(user_id)
        status_results = {}

        # Check OpenAI status
        openai_key = None
        for key in user_keys:
            if key['service_name'] == 'openai' and key['is_active']:
                openai_key = key['api_key']
                break

        if openai_key:
            try:
                import openai
                openai.api_key = openai_key
                # Test with a minimal request
                openai.completions.create(
                    model="text-davinci-003",
                    prompt="test",
                    max_tokens=5
                )
                status_results['openai'] = {'status': 'connected', 'message': 'API key is valid'}
            except Exception as e:
                status_results['openai'] = {'status': 'disconnected', 'message': str(e)}
        else:
            status_results['openai'] = {'status': 'disconnected', 'message': 'No API key configured'}

        # Check WordPress status
        wp_url = None
        wp_username = None
        wp_password = None
        from app.models import user_settings_manager
        user_settings = user_settings_manager.get_user_settings(user_id)
        if user_settings:
            wp_url = user_settings.get('wordpress_url')
            wp_username = user_settings.get('wordpress_username')
            wp_app_password = user_settings.get('wordpress_app_password')

        if wp_url and wp_username and wp_app_password:
            try:
                import requests
                from requests.auth import HTTPBasicAuth

                # Test WordPress connection
                response = requests.get(
                    f"{wp_url}/wp-json/wp/v2/users/me",
                    auth=HTTPBasicAuth(wp_username, wp_app_password),
                    timeout=10
                )
                if response.status_code == 200:
                    status_results['wordpress'] = {'status': 'connected', 'message': 'Connected successfully'}
                else:
                    status_results['wordpress'] = {'status': 'disconnected', 'message': f'HTTP {response.status_code}'}
            except Exception as e:
                status_results['wordpress'] = {'status': 'disconnected', 'message': str(e)}
        else:
            status_results['wordpress'] = {'status': 'disconnected', 'message': 'WordPress credentials not configured'}

        # Check SEMrush status
        semrush_key = None
        for key in user_keys:
            if key['service_name'] == 'semrush' and key['is_active']:
                semrush_key = key['api_key']
                break

        if semrush_key:
            try:
                import requests
                # Test SEMrush API
                response = requests.get(
                    f"https://api.semrush.com/?key={semrush_key}&type=phrase_this&phrase=test&database=us",
                    timeout=10
                )
                if response.status_code == 200:
                    status_results['semrush'] = {'status': 'connected', 'message': 'API key is valid'}
                else:
                    status_results['semrush'] = {'status': 'disconnected', 'message': f'HTTP {response.status_code}'}
            except Exception as e:
                status_results['semrush'] = {'status': 'disconnected', 'message': str(e)}
        else:
            status_results['semrush'] = {'status': 'disconnected', 'message': 'No API key configured'}

        # Check Google Analytics status
        ga4_id = user_settings.get('ga4_property_id') if user_settings else None
        if ga4_id:
            # For now, just check if GA4 ID is configured
            status_results['google_analytics'] = {'status': 'connected', 'message': 'Property ID configured'}
        else:
            status_results['google_analytics'] = {'status': 'disconnected', 'message': 'Property ID not configured'}

        return jsonify(status_results)

    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger()
        logger.error(f"Error checking API status: {str(e)}")
        return jsonify({'error': 'Failed to check API status'}), 500
