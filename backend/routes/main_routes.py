from flask import Blueprint, jsonify, request
from sqlalchemy import func
from datetime import datetime, timezone

from models import User, UserProfile
from extensions import db

main_bp = Blueprint('main_bp', __name__, url_prefix='/api')

@main_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

@main_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard_data(user_id): # user_id is already a parameter
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        dashboard_data = {
            'user': {
                'user_id': user.user_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'profile': profile.to_dict() if profile else None
            },
            'stats': {
                'message': 'Interview statistics are currently unavailable due to missing data models.',
                'interviewsCompleted': 0,
                'averageScore': 0,
                'upcomingInterviews': 0,
                'practiceTime': "0h 0m",
                'activities': [{'id': None, 'type': 'account_creation', 'completed': True, 'date': user.created_at.isoformat() if user.created_at else None}],
                'recommendedPractice': [
                    {'id': 1, 'title': 'Behavioral Interview', 'description': 'Practice common behavioral questions.', 'type': 'behavioral'},
                    {'id': 2, 'title': 'Technical Skills', 'description': 'Practice technical questions for your role.', 'type': 'technical'}
                ],
                'chartData': []
            }
        }
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        print(f"Dashboard Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@main_bp.route('/seed/<int:user_id>', methods=['POST'])
def seed_data(user_id): # user_id is already a parameter
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found for seeding'}), 404
        
    return jsonify({
        'success': False,
        'message': 'Seeding feature is currently unavailable due to missing data models (InterviewSession, etc.).',
    }), 501