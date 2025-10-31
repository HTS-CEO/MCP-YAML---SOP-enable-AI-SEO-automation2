from flask import Blueprint, request, jsonify, session
from app.services.wordpress_service import WordPressService
from app.services.semrush_service import SEMrushService
from app.services.openai_service import OpenAIService
from app.utils.auth import token_required
from app.utils.logger import get_logger
import sqlite3

reoptimize_bp = Blueprint('reoptimize', __name__)
logger = get_logger()

@reoptimize_bp.route('/reoptimize', methods=['POST'])
@token_required
def reoptimize_post():
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        keywords = data.get('keywords', '')

        if not post_id:
            return jsonify({'error': 'Post ID is required'}), 400

        # Check SEMrush ranking
        semrush_service = SEMrushService()
        ranking_data = semrush_service.get_keyword_ranking(keywords or 'default')

        if ranking_data.get('position', 100) > 10:  # If not in top 10
            # Fetch existing post
            wordpress_service = WordPressService()
            existing_post = wordpress_service.get_post(post_id)

            # Re-optimize with OpenAI
            openai_service = OpenAIService(user_id=session.get('user_id'))
            optimized_content = openai_service.reoptimize_content(
                existing_post['content'],
                keywords or existing_post.get('keywords', '')
            )

            # Update post
            update_data = {
                'title': optimized_content['title'],
                'content': optimized_content['content'],
                'meta': {
                    'seo_title': optimized_content['seo_title'],
                    'seo_description': optimized_content['seo_description']
                }
            }

            wordpress_service.update_post(post_id, update_data)

            # Update database
            conn = sqlite3.connect('seo_automation.db')
            c = conn.cursor()
            c.execute('''UPDATE posts SET content = ?, keywords = ? WHERE wordpress_id = ?''',
                      (optimized_content['content'], keywords, post_id))
            conn.commit()
            conn.close()

            logger.info(f"Post re-optimized: {post_id}")
            return jsonify({
                'post_id': post_id,
                'ranking_change': f"Optimized for better ranking (was position {ranking_data.get('position', 'N/A')})"
            })
        else:
            return jsonify({
                'message': 'Post is already well-ranked, no optimization needed',
                'current_position': ranking_data.get('position')
            })

    except Exception as e:
        logger.error(f"Error re-optimizing post: {str(e)}")
        return jsonify({'error': str(e)}), 500
