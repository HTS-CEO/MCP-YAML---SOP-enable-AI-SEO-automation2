from flask import Blueprint, request, jsonify
from app.services.google_service import GoogleService
from app.utils.auth import token_required
from app.utils.logger import get_logger

gbp_bp = Blueprint('gbp', __name__)
logger = get_logger()

@gbp_bp.route('/gbp_post', methods=['POST'])
@token_required
def create_gbp_post():
    try:
        data = request.get_json()
        content = data.get('content')
        image_url = data.get('image_url')
        cta_url = data.get('cta_url')

        if not content:
            return jsonify({'error': 'Content is required'}), 400

        if len(content) > 1500:  # GBP limit
            return jsonify({'error': 'Content must be 1500 characters or less'}), 400

        google_service = GoogleService()
        post_data = {
            'content': content,
            'image_url': image_url,
            'cta_url': cta_url
        }

        result = google_service.create_gbp_post(post_data)

        logger.info(f"GBP post created: {result.get('post_id')}")
        return jsonify({
            'post_id': result.get('post_id'),
            'status': 'published',
            'message': 'Successfully published to Google Business Profile'
        })

    except Exception as e:
        logger.error(f"Error creating GBP post: {str(e)}")
        return jsonify({'error': str(e)}), 500