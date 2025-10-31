from flask import Blueprint, request, jsonify, session
from app.services.wordpress_service import WordPressService
from app.services.openai_service import OpenAIService
from app.utils.auth import token_required
from app.utils.logger import get_logger
import sqlite3
from datetime import datetime

blog_bp = Blueprint('blog', __name__)
logger = get_logger()

@blog_bp.route('/generate_blog', methods=['POST'])
@token_required
def generate_blog():
    try:
        data = request.get_json()
        keyword = data.get('keyword')
        secondary_keywords = data.get('secondary_keywords', '')

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        # Generate content with OpenAI
        openai_service = OpenAIService(user_id=session.get('user_id'))
        blog_content = openai_service.generate_blog_post(keyword, secondary_keywords)

        # Post to WordPress
        wordpress_service = WordPressService()
        post_data = {
            'title': blog_content['title'],
            'content': blog_content['content'],
            'status': 'draft',
            'meta': {
                'seo_title': blog_content['seo_title'],
                'seo_description': blog_content['seo_description'],
                'keywords': keyword + (', ' + secondary_keywords if secondary_keywords else '')
            }
        }

        post_result = wordpress_service.create_post(post_data)

        # Save to database
        conn = sqlite3.connect('seo_automation.db')
        c = conn.cursor()
        c.execute('''INSERT INTO posts (wordpress_id, title, content, keywords, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (post_result['id'], post_data['title'], post_data['content'],
                   keyword + (', ' + secondary_keywords if secondary_keywords else ''),
                   datetime.now()))
        conn.commit()
        conn.close()

        logger.info(f"Blog post generated and posted: {post_result['id']}")
        return jsonify({
            'post_id': post_result['id'],
            'title': post_data['title'],
            'status': 'draft'
        })

    except Exception as e:
        logger.error(f"Error generating blog: {str(e)}")
        return jsonify({'error': str(e)}), 500
