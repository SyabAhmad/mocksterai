from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta

from models import User, UserProfile, UserAuthLog
from extensions import db

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    required_fields = ['firstName', 'lastName', 'email', 'password', 'confirmPassword', 
                       'occupation', 'industry', 'experienceLevel']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    if data['password'] != data['confirmPassword']:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if not data.get('agreeToTerms'): # Ensure this is handled by frontend or make non-optional
        return jsonify({'error': 'You must agree to the terms and conditions'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    try:
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        db.session.add(new_user)
        db.session.flush() # To get new_user.user_id

        new_profile = UserProfile(
            user_id=new_user.user_id,
            occupation=data['occupation'],
            industry=data['industry'],
            experience_level=data['experienceLevel'],
            interview_goal=data.get('interviewGoal', '')
        )
        db.session.add(new_profile)
        
        log_entry = UserAuthLog(
            user_id=new_user.user_id,
            action='SIGNUP',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log_entry)
        db.session.commit()
        
        user_data_to_return = new_user.to_dict()
        user_data_to_return['profile'] = new_profile.to_dict()

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_data_to_return # Return user data including profile
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Log error e for server-side debugging
        print(f"Signup Error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password are required'}), 400
    
    try:
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            # Generic error message for security
            # Log failed attempt internally
            log_action = 'LOGIN_FAILED_USER_NOT_FOUND' if not user else 'LOGIN_FAILED_PASSWORD_MISMATCH'
            user_id_for_log = user.user_id if user else None

            log_entry = UserAuthLog(
                user_id=user_id_for_log,
                action=log_action,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user.last_login_at = datetime.now(timezone.utc)
        
        log_entry = UserAuthLog(
            user_id=user.user_id,
            action='LOGIN_SUCCESS',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log_entry)
        db.session.commit()
        
        profile = UserProfile.query.filter_by(user_id=user.user_id).first()
        user_data = user.to_dict()
        user_data['profile'] = profile.to_dict() if profile else None
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_data,
            # 'token': token, # REMOVED
            # 'expires_at': token_expiration.isoformat() # REMOVED
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Login Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# @auth_bp.route('/verify', methods=['GET']) # REMOVE this entire route
# def verify_user_token():
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith('Bearer '):
#         return jsonify({'error': 'Invalid or missing token', 'code': 'token_missing'}), 401
    
#     token = auth_header.split(' ')[1]
    
#     try:
#         payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
#         user_id = payload.get('user_id')
        
#         # Check 'exp' claim
#         if 'exp' not in payload or datetime.fromtimestamp(payload['exp'], tz=timezone.utc) < datetime.now(timezone.utc):
#              return jsonify({'error': 'Token expired', 'code': 'token_expired'}), 401

#         user = User.query.get(int(user_id))
#         if not user:
#             return jsonify({'error': 'User not found', 'code': 'user_not_found'}), 404
            
#         return jsonify({
#             'authenticated': True,
#             'user_id': user.user_id,
#             'first_name': user.first_name,
#             'last_name': user.last_name,
#             'email': user.email,
#             'token_expires_at': datetime.fromtimestamp(payload['exp'], tz=timezone.utc).isoformat()
#         }), 200
        
#     except jwt.ExpiredSignatureError:
#         return jsonify({'error': 'Token expired', 'code': 'token_expired'}), 401
#     except jwt.InvalidTokenError:
#         return jsonify({'error': 'Invalid token', 'code': 'invalid_token'}), 401
#     except Exception as e:
#         print(f"Token Verification Error: {str(e)}")
#         return jsonify({'error': f'Authentication error: {str(e)}', 'code': 'auth_error'}), 401