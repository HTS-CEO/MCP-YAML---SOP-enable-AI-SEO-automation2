from flask import Flask, make_response, request, jsonify, send_from_directory, session, flash, redirect, url_for, render_template
from flask_cors import CORS
from flask_session import Session
import os
from dotenv import load_dotenv
from app.routes.blog import blog_bp
from app.routes.reoptimize import reoptimize_bp
from app.routes.gbp import gbp_bp
from app.routes.report import report_bp
from app.routes.auth import auth_bp, admin_required
from app.utils.logger import setup_logger, log_and_notify
from app.utils.auth import token_required
from app.models import db_manager, user_manager
import sqlite3
from datetime import datetime
from scheduler import start_scheduler
from flask_cors import CORS
from flask_session import Session
import os
from dotenv import load_dotenv
from app.routes.blog import blog_bp
from app.routes.reoptimize import reoptimize_bp
from app.routes.gbp import gbp_bp
from app.routes.report import report_bp
from app.routes.auth import auth_bp, admin_required
from app.utils.logger import setup_logger, log_and_notify
from app.utils.auth import token_required
from app.models import db_manager, user_manager
import sqlite3
from datetime import datetime
from scheduler import start_scheduler

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure session
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_KEY_PREFIX'] = os.getenv('SESSION_KEY_PREFIX', 'seo_automation_')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this-in-production')
Session(app)

# Setup logging
logger = setup_logger()

# Initialize database (now handled by models.py)
try:
    db_manager  # This will initialize the database
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    # Continue without database for now

# Register blueprints
app.register_blueprint(blog_bp, url_prefix='/api')
app.register_blueprint(reoptimize_bp, url_prefix='/api')
app.register_blueprint(gbp_bp, url_prefix='/api')
app.register_blueprint(report_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='')

@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code} for {request.path}")
    return response

@app.route('/')
def landing():
    session.clear()
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/reoptimize')
def reoptimize():
    return render_template('reoptimize.html')

@app.route('/gbp')
def gbp():
    return render_template('gbp.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/admin')
@admin_required
def admin():
    users = user_manager.get_all_users()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    users = user_manager.get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/api-keys')
@admin_required
def admin_api_keys():
    return render_template('admin_api_keys.html')

@app.route('/admin/logs')
@admin_required
def admin_logs():
    return render_template('admin_logs.html')

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin_settings.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.html'):
        return send_from_directory('templates', filename)
    return jsonify({'error': 'File not found'}), 404

@app.errorhandler(404)
def not_found(error):
    log_and_notify(f"404 Error: {request.path}", level='warning')
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    log_and_notify(f"500 Internal Error: {str(error)}", level='error', notify_slack=True)
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    log_and_notify(f"Unhandled exception: {str(error)}", level='error', notify_slack=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500

# Start background scheduler (only in development, disable for production)
if os.getenv('ENVIRONMENT') != 'production' and os.getenv('RENDER') != 'true':
    scheduler = start_scheduler()
else:
    scheduler = None

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8000))
        app.run(debug=False, host='0.0.0.0', port=port)
    finally:
        if scheduler:
            from scheduler import stop_scheduler
            stop_scheduler(scheduler)
