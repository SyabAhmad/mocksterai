from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from models import User, UserProfile
from extensions import db

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/user')

@user_bp.route('/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
            
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    user_data = user.to_dict()
    user_data['profile'] = profile.to_dict() if profile else None
        
    return jsonify(user_data), 200

@user_bp.route('/<int:user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    if 'first_name' in data: user.first_name = data['first_name']
    if 'last_name' in data: user.last_name = data['last_name']
    
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)
    
    profile_fields = ['occupation', 'industry', 'experience_level', 'interview_goal', 
                      'skills', 'location', 'linkedin_url', 'github_url', 'portfolio_url', 'bio']
    for field in profile_fields:
        if field in data:
            setattr(profile, field, data[field])
            
    profile.updated_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.session.commit()
        updated_user_data = user.to_dict()
        updated_user_data['profile'] = profile.to_dict()
        return jsonify(updated_user_data), 200
    except Exception as e:
        db.session.rollback()
        print(f"Profile Update Error: {str(e)}")
        return jsonify({'error': f'Profile update error: {str(e)}'}), 500