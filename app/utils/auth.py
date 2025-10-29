from functools import wraps
from flask import request, jsonify
import os
from app.utils.logger import log_and_notify

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_token = request.headers.get('Authorization')

        if not auth_token:
            log_and_notify("Missing authorization token", level='warning')
            return jsonify({'error': 'Authorization token required'}), 401

        # Extract token from "Bearer <token>"
        try:
            token_type, token = auth_token.split(' ', 1)
            if token_type.lower() != 'bearer':
                raise ValueError("Invalid token type")
        except ValueError:
            log_and_notify("Invalid authorization header format", level='warning')
            return jsonify({'error': 'Invalid authorization header'}), 401

        expected_token = os.getenv('AUTH_TOKEN')
        if not expected_token:
            log_and_notify("AUTH_TOKEN not configured", level='error', notify_slack=True)
            return jsonify({'error': 'Server configuration error'}), 500

        if token != expected_token:
            log_and_notify("Invalid authorization token", level='warning')
            return jsonify({'error': 'Invalid authorization token'}), 401

        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            log_and_notify("Missing API key", level='warning')
            return jsonify({'error': 'API key required'}), 401

        expected_key = os.getenv('API_KEY')
        if not expected_key:
            log_and_notify("API_KEY not configured", level='error', notify_slack=True)
            return jsonify({'error': 'Server configuration error'}), 500

        if api_key != expected_key:
            log_and_notify("Invalid API key", level='warning')
            return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return decorated_function

def validate_payload(required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'error': 'JSON payload required'}), 400

            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None or str(data[field]).strip() == '':
                    missing_fields.append(field)

            if missing_fields:
                return jsonify({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator