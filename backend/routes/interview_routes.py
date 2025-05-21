from flask import Blueprint, request, jsonify # g removed
import json
import os
from datetime import datetime, timezone

from extensions import db
from models import User 
from Services.groq_service import GroqService
from config import Config
# from ..utils import token_required, get_most_common_items # token_required removed
from utils import get_most_common_items


interview_bp = Blueprint('interview_bp', __name__, url_prefix='/api/interview')

groq_service = GroqService(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None

@interview_bp.route('/generate-questions', methods=['POST'])
# @token_required # REMOVED
def generate_interview_questions():
    # user_id = g.user_id # REMOVED - if needed, frontend must send it in 'data'
    # Example: data = request.get_json(); user_id = data.get('user_id')
    if not groq_service:
        return jsonify({'error': 'Groq service not configured. Missing API Key.'}), 503

    data = request.get_json()
    if not data or not data.get('jobTitle') or not data.get('interviewType'):
        return jsonify({'error': 'Missing required fields: jobTitle and interviewType'}), 400

    try:
        questions = groq_service.generate_interview_questions(data)
        # Potentially save questions linked to user_id if provided
        return jsonify({'questions': questions}), 200
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        fallback_questions = [
            {"id": 1, "question": "Tell me about yourself.", "importance": "Basic introduction.", "tips": "Be concise and relevant.", "interviewer_expectations": "Clear and confident introduction."},
            {"id": 2, "question": "What are your strengths?", "importance": "Assess key skills.", "tips": "Focus on 2-3 strengths.", "interviewer_expectations": "Relevant strengths for the role."},
        ]
        return jsonify({'questions': fallback_questions, 'message': 'Using fallback questions due to an error.'}), 200

@interview_bp.route('/analyze-response', methods=['POST'])
# @token_required # REMOVED
def analyze_interview_response():
    # user_id = g.user_id # REMOVED - if needed, frontend must send it
    if not groq_service:
        return jsonify({'error': 'Groq service not configured. Missing API Key.'}), 503
        
    interview_id_form = request.form.get('interview_id') 
    question_index = request.form.get('question_index')
    answer_text = request.form.get('answer')
    
    if not interview_id_form or question_index is None or not answer_text: # interview_id from form
        return jsonify({'error': 'Interview ID, question index, and answer are required'}), 400
    
    session_completed_status = False 

    try:
        question_data_json = request.form.get('question', '{}')
        job_context_json = request.form.get('job_context', '{}')
        
        try:
            question_data = json.loads(question_data_json)
            job_context = json.loads(job_context_json)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON format for question or job_context'}), 400

        if not question_data.get('question'):
             return jsonify({'error': 'Question text missing in question_data'}), 400

        feedback = groq_service.analyze_interview_response(
            question=question_data, 
            answer=answer_text,
            job_context=job_context
        )
        
        # Logic for saving to DB would need user_id from request if it's user-specific
        
        return jsonify({
            'feedback': feedback,
            'is_complete': session_completed_status 
        }), 200
    
    except Exception as e:
        # db.session.rollback() # Only if db operations were attempted
        print(f"Error analyzing response: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze response',
            'details': str(e)
        }), 500

@interview_bp.route('/performance-history', methods=['GET'])
# @token_required # REMOVED
def get_performance_history():
    # This route now needs user_id, e.g., /api/interview/performance-history/<user_id>
    # Or user_id as a query parameter: /api/interview/performance-history?user_id=...
    # For now, returning a generic message as user_id is not passed.
    # user_id = g.user_id # REMOVED
    user_id_param = request.args.get('user_id') # Example: frontend sends as query param
    if not user_id_param:
        return jsonify({'error': 'User ID is required for performance history'}), 400
    
    # Actual logic to fetch history for user_id_param would go here
    return jsonify({
        'message': f'Performance history feature for user {user_id_param} is currently unavailable or needs user_id.',
        'total_interviews': 0,
        'avg_score': 0,
        'total_practice_time': 0,
        'history': [],
        'common_strengths': [],
        'common_improvements': []
    }), 200