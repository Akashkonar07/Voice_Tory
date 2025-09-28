from flask import Blueprint, request, jsonify
from src.backend.db.models import InventoryDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize database
db = InventoryDatabase()

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Handle user registration."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract required fields
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        # Validate required fields
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Username, email, and password are required'
            }), 400
        
        # Create user
        result = db.create_user(username, email, password, full_name)
        
        if result['success']:
            logger.info(f"User created successfully: {username}")
            return jsonify({
                'success': True,
                'message': 'User created successfully',
                'user_id': str(result['user_id']),
                'username': result['username'],
                'email': result['email']
            }), 201
        else:
            logger.warning(f"User creation failed: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract required fields
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate required fields
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # Authenticate user
        auth_result = db.authenticate_user(username, password)
        
        if auth_result['success']:
            # Create session
            session_result = db.create_session(
                auth_result['user_id'],
                auth_result['username']
            )
            
            if session_result['success']:
                logger.info(f"User logged in successfully: {username}")
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'session_token': session_result['session_token'],
                    'expires_at': session_result['expires_at'].isoformat(),
                    'user_id': str(auth_result['user_id']),
                    'username': auth_result['username'],
                    'email': auth_result['email'],
                    'full_name': auth_result['full_name'],
                    'role': auth_result['role']
                }), 200
            else:
                logger.error(f"Session creation failed: {session_result['error']}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to create session'
                }), 500
        else:
            logger.warning(f"Login failed for {username}: {auth_result['error']}")
            return jsonify({
                'success': False,
                'error': auth_result['error']
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/validate', methods=['POST'])
def validate_session():
    """Validate session token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        session_token = data.get('session_token', '').strip()
        
        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Session token is required'
            }), 400
        
        # Validate session
        result = db.validate_session(session_token)
        
        if result['success']:
            logger.info(f"Session validated for user: {result['username']}")
            return jsonify({
                'success': True,
                'message': 'Session is valid',
                'user_id': str(result['user_id']),
                'username': result['username']
            }), 200
        else:
            logger.warning(f"Session validation failed: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
            
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        session_token = data.get('session_token', '').strip()
        
        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Session token is required'
            }), 400
        
        # Delete session
        result = db.delete_session(session_token)
        
        if result['success']:
            logger.info("User logged out successfully")
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            }), 200
        else:
            logger.warning(f"Logout failed: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile information."""
    try:
        # Get session token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header'
            }), 401
        
        session_token = auth_header[7:].strip()
        
        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Session token is required'
            }), 400
        
        # Validate session
        session_result = db.validate_session(session_token)
        
        if not session_result['success']:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 401
        
        # Get user information from database
        user = db.users.find_one({'_id': session_result['user_id']})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Return user profile (excluding sensitive information)
        return jsonify({
            'success': True,
            'user': {
                'user_id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user.get('role', 'user'),
                'created_at': user['created_at'].isoformat(),
                'is_active': user.get('is_active', True)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Middleware function to check authentication
def require_auth(f):
    """Decorator to require authentication for routes."""
    def decorated_function(*args, **kwargs):
        session_token = None
        
        # Try to get session token from Authorization header first
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:].strip()
        
        # For GET requests (page loads), also check query parameters
        if not session_token and request.method == 'GET':
            session_token = request.args.get('session_token')
        
        # For POST requests, check request body
        if not session_token and request.method == 'POST' and request.is_json:
            data = request.get_json()
            if data:
                session_token = data.get('session_token')
        
        if not session_token:
            # For page requests, redirect to login instead of returning JSON
            if request.method == 'GET' and not request.path.startswith('/api/'):
                from flask import redirect
                return redirect('/login')
            else:
                return jsonify({
                    'success': False,
                    'error': 'Authorization required'
                }), 401
        
        # Validate session
        result = db.validate_session(session_token)
        
        if not result['success']:
            # For page requests, redirect to login instead of returning JSON
            if request.method == 'GET' and not request.path.startswith('/api/'):
                from flask import redirect
                return redirect('/login')
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 401
        
        # Add user info to request context
        request.user = {
            'user_id': result['user_id'],
            'username': result['username']
        }
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function
