import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from flask import request
import jwt
import os
from datetime import datetime, timedelta
from app.utils.logger import get_logger
from urllib.parse import urlparse

logger = get_logger()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            logger.warning("DATABASE_URL environment variable is not set. Database operations will be disabled.")
            return
        try:
            self.init_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            # Don't raise exception to allow app to start even if DB is not ready
            pass

    def get_connection(self):
        if not self.database_url:
            raise ValueError("Database URL is not configured")
        return psycopg2.connect(self.database_url)

    def init_database(self):
        """Initialize all database tables"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()

            # Users table
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                api_calls_count INTEGER DEFAULT 0,
                subscription_plan VARCHAR(50) DEFAULT 'free'
            )''')

            # User API Keys table
            c.execute('''CREATE TABLE IF NOT EXISTS user_api_keys (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                service_name VARCHAR(255) NOT NULL,
                api_key TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )''')

            # Global API Keys (managed by admin)
            c.execute('''CREATE TABLE IF NOT EXISTS global_api_keys (
                id SERIAL PRIMARY KEY,
                service_name VARCHAR(255) UNIQUE NOT NULL,
                api_key TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Posts table (existing)
            c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users (id),
                wordpress_id INTEGER,
                title TEXT,
                content TEXT,
                keywords TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # User Sessions
            c.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                session_token TEXT UNIQUE NOT NULL,
                ip_address VARCHAR(255),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )''')

            # Activity Logs
            c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users (id),
                action VARCHAR(255) NOT NULL,
                details TEXT,
                ip_address VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Insert default admin user if not exists
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@seoautomation.com')

            c.execute('SELECT id FROM users WHERE username = %s', (admin_username,))
            if not c.fetchone():
                password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                c.execute('''INSERT INTO users (username, email, password_hash, role, subscription_plan)
                            VALUES (%s, %s, %s, 'admin', 'enterprise')''',
                         (admin_username, admin_email, password_hash))
                logger.info(f"Created default admin user: {admin_username}")

            # Note: Default API keys are no longer inserted automatically
            # Admin will add them manually through the admin interface

            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
        finally:
            if conn:
                conn.close()

class UserManager:
    def __init__(self):
        self.db = DatabaseManager()

    def _check_db_connection(self):
        """Check if database is configured"""
        if not self.db.database_url:
            return False
        return True

    def create_user(self, username, email, password, role='user', subscription_plan='free'):
        """Create a new user"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            # Check if user already exists
            c.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
            if c.fetchone():
                return {'error': 'User already exists'}

            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Create user
            c.execute('''INSERT INTO users (username, email, password_hash, role, subscription_plan)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id''',
                     (username, email, password_hash, role, subscription_plan))

            user_id = c.fetchone()[0]
            conn.commit()
            conn.close()

            logger.info(f"User created: {username} (ID: {user_id})")
            return {'success': True, 'user_id': user_id}

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {'error': str(e)}

    def authenticate_user(self, username_or_email, password):
        """Authenticate user login"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            c.execute('''SELECT id, username, email, password_hash, role, is_active
                        FROM users WHERE (username = %s OR email = %s) AND is_active = TRUE''',
                     (username_or_email, username_or_email))

            user = c.fetchone()
            conn.close()

            if not user:
                return {'error': 'User not found'}

            user_id, username, email, password_hash, role, is_active = user

            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Update last login
                self.update_last_login(user_id)

                # Log activity
                remote_addr = request.remote_addr if 'request' in globals() else "unknown"
                self.log_activity(user_id, 'login', f'User logged in from {remote_addr}')

                return {
                    'success': True,
                    'user': {
                        'id': user_id,
                        'username': username,
                        'email': email,
                        'role': role
                    }
                }
            else:
                return {'error': 'Invalid password'}

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return {'error': str(e)}

    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        if not self._check_db_connection():
            return None

        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('SELECT id, username, email, role, is_active, created_at, last_login, subscription_plan FROM users WHERE id = %s', (user_id,))
            user = c.fetchone()
            conn.close()

            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': user[4],
                    'created_at': user[5],
                    'last_login': user[6],
                    'subscription_plan': user[7]
                }
            return None

        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    def get_all_users(self):
        """Get all users (admin only)"""
        if not self._check_db_connection():
            return []

        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('SELECT id, username, email, role, is_active, created_at, last_login, subscription_plan FROM users ORDER BY created_at DESC')
            users = c.fetchall()
            conn.close()

            return [{
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'is_active': user[4],
                'created_at': user[5],
                'last_login': user[6],
                'subscription_plan': user[7]
            } for user in users]

        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []

    def update_user(self, user_id, updates):
        """Update user information"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            update_fields = []
            values = []

            for field, value in updates.items():
                if field in ['username', 'email', 'role', 'is_active', 'subscription_plan']:
                    update_fields.append(f"{field} = %s")
                    values.append(value)

            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                values.append(user_id)
                c.execute(query, tuple(values))
                conn.commit()

            conn.close()
            logger.info(f"User updated: {user_id}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return {'error': str(e)}

    def delete_user(self, user_id):
        """Delete user (admin only)"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            # Check if user exists
            c.execute('SELECT id FROM users WHERE id = %s', (user_id,))
            if not c.fetchone():
                return {'error': 'User not found'}

            # Delete related records first (cascade delete)
            c.execute('DELETE FROM user_api_keys WHERE user_id = %s', (user_id,))
            c.execute('DELETE FROM user_sessions WHERE user_id = %s', (user_id,))
            c.execute('DELETE FROM activity_logs WHERE user_id = %s', (user_id,))
            # Note: posts table doesn't have user_id column, skip it

            # Delete the user
            c.execute('DELETE FROM users WHERE id = %s', (user_id,))
            deleted = c.rowcount > 0

            conn.commit()
            conn.close()

            if deleted:
                logger.info(f"User deleted: {user_id}")
                return {'success': True}
            else:
                return {'error': 'User not found'}

        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return {'error': str(e)}

    def log_activity(self, user_id, action, details=''):
        """Log user activity"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO activity_logs (user_id, action, details, ip_address)
                        VALUES (%s, %s, %s, %s)''',
                     (user_id, action, details, request.remote_addr if 'request' in globals() else 'unknown'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

class APIKeyManager:
    def __init__(self):
        self.db = DatabaseManager()

    def _check_db_connection(self):
        """Check if database is configured"""
        if not self.db.database_url:
            return False
        return True

    def set_user_api_key(self, user_id, service_name, api_key):
        """Set API key for a specific user"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            # Check if key already exists
            c.execute('''SELECT id FROM user_api_keys
                        WHERE user_id = %s AND service_name = %s''', (user_id, service_name))

            existing = c.fetchone()

            if existing:
                # Update existing key
                c.execute('''UPDATE user_api_keys SET api_key = %s, updated_at = CURRENT_TIMESTAMP
                           WHERE user_id = %s AND service_name = %s''',
                         (api_key, user_id, service_name))
            else:
                # Insert new key
                c.execute('''INSERT INTO user_api_keys (user_id, service_name, api_key)
                           VALUES (%s, %s, %s)''', (user_id, service_name, api_key))

            conn.commit()
            conn.close()

            logger.info(f"User API key set: {service_name} for user {user_id}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error setting user API key: {str(e)}")
            return {'error': str(e)}

    def get_user_api_keys(self, user_id):
        """Get all API keys for a user"""
        if not self._check_db_connection():
            return []

        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('''SELECT service_name, api_key, is_active, created_at, last_used, usage_count
                        FROM user_api_keys WHERE user_id = %s''', (user_id,))
            keys = c.fetchall()
            conn.close()

            return [{
                'service_name': key[0],
                'api_key': key[1],
                'is_active': key[2],
                'created_at': key[3],
                'last_used': key[4],
                'usage_count': key[5]
            } for key in keys]

        except Exception as e:
            logger.error(f"Error getting user API keys: {str(e)}")
            return []

    def get_global_api_keys(self):
        """Get all global API keys (admin only)"""
        if not self._check_db_connection():
            return []

        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('SELECT service_name, api_key, description, is_active, created_at FROM global_api_keys')
            keys = c.fetchall()
            conn.close()

            return [{
                'service_name': key[0],
                'api_key': key[1],
                'description': key[2],
                'is_active': key[3],
                'created_at': key[4]
            } for key in keys]

        except Exception as e:
            logger.error(f"Error getting global API keys: {str(e)}")
            return []

    def update_global_api_key(self, service_name, api_key, description=''):
        """Update global API key (admin only)"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            c.execute('''INSERT INTO global_api_keys
                         (service_name, api_key, description, updated_at)
                         VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                         ON CONFLICT (service_name) DO UPDATE SET
                         api_key = EXCLUDED.api_key,
                         description = EXCLUDED.description,
                         updated_at = EXCLUDED.updated_at''',
                      (service_name, api_key, description))

            conn.commit()
            conn.close()

            logger.info(f"Global API key updated: {service_name}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error updating global API key: {str(e)}")
            return {'error': str(e)}

    def delete_user_api_key(self, user_id, service_name):
        """Delete a user's API key"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            c.execute('''DELETE FROM user_api_keys
                         WHERE user_id = %s AND service_name = %s''',
                      (user_id, service_name))

            deleted = c.rowcount > 0
            conn.commit()
            conn.close()

            if deleted:
                logger.info(f"User API key deleted: {service_name} for user {user_id}")
                return {'success': True}
            else:
                return {'error': 'API key not found'}

        except Exception as e:
            logger.error(f"Error deleting user API key: {str(e)}")
            return {'error': str(e)}

    def delete_global_api_key(self, service_name):
        """Delete a global API key"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            c.execute('''DELETE FROM global_api_keys
                         WHERE service_name = %s''',
                      (service_name,))

            deleted = c.rowcount > 0
            conn.commit()
            conn.close()

            if deleted:
                logger.info(f"Global API key deleted: {service_name}")
            else:
                logger.info(f"Global API key not found for deletion: {service_name}")

            return {'success': True}

        except Exception as e:
            logger.error(f"Error deleting global API key: {str(e)}")
            return {'error': str(e)}

class SessionManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')

    def _check_db_connection(self):
        """Check if database is configured"""
        if not self.db.database_url:
            return False
        return True

    def create_session(self, user_id, ip_address='', user_agent=''):
        """Create a new session for user"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            import uuid
            session_token = str(uuid.uuid4())

            # Create JWT token
            import jwt
            payload = {
                'user_id': user_id,
                'session_token': session_token,
                'exp': datetime.utcnow() + timedelta(days=7)  # 7 days expiry
            }
            jwt_token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')

            conn = self.db.get_connection()
            c = conn.cursor()

            expires_at = datetime.now() + timedelta(days=7)
            c.execute('''INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
                        VALUES (%s, %s, %s, %s, %s)''',
                     (user_id, session_token, ip_address, user_agent, expires_at))

            conn.commit()
            conn.close()

            logger.info(f"Session created for user: {user_id}")
            return {'success': True, 'token': jwt_token, 'session_token': session_token}

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return {'error': str(e)}

    def validate_session(self, token):
        """Validate JWT session token"""
        if not self._check_db_connection():
            return {'valid': False, 'error': 'Database not configured'}

        try:
            import jwt
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])

            user_id = payload['user_id']
            session_token = payload['session_token']

            # Check if session exists and is active
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('''SELECT id FROM user_sessions
                        WHERE user_id = %s AND session_token = %s AND is_active = 1 AND expires_at > CURRENT_TIMESTAMP''',
                     (user_id, session_token))

            session = c.fetchone()
            conn.close()

            if session:
                return {'valid': True, 'user_id': user_id}
            else:
                return {'valid': False, 'error': 'Session expired or invalid'}

        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return {'valid': False, 'error': 'Session validation error'}

    def destroy_session(self, user_id, session_token):
        """Destroy user session"""
        if not self._check_db_connection():
            return {'error': 'Database not configured'}

        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = %s AND session_token = %s',
                      (user_id, session_token))
            conn.commit()
            conn.close()

            logger.info(f"Session destroyed for user: {user_id}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error destroying session: {str(e)}")
            return {'error': str(e)}

# Global instances
db_manager = DatabaseManager()
user_manager = UserManager()
api_key_manager = APIKeyManager()
session_manager = SessionManager()
