from flask import Blueprint, request, jsonify
from app.services.wordpress_service import WordPressService
from app.services.semrush_service import SEMrushService
from app.services.google_service import GoogleService
from app.services.report_service import ReportService
from app.utils.auth import token_required
from app.utils.logger import get_logger

report_bp = Blueprint('report', __name__)
logger = get_logger()

@report_bp.route('/report', methods=['GET'])
@token_required
def generate_report():
    try:
        # Get data from all services
        wordpress_service = WordPressService()
        semrush_service = SEMrushService()
        google_service = GoogleService()

        wordpress_data = wordpress_service.get_stats()
        semrush_data = semrush_service.get_stats()
        ga4_data = google_service.get_ga4_stats()
        gbp_data = google_service.get_gbp_stats()

        # Generate comprehensive report
        report_service = ReportService()
        report = report_service.generate_report({
            'wordpress': wordpress_data,
            'semrush': semrush_data,
            'ga4': ga4_data,
            'gbp': gbp_data
        })

        logger.info("Report generated successfully")
        return jsonify(report)

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/dashboard_stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    try:
        # Simplified stats for dashboard
        wordpress_service = WordPressService()
        semrush_service = SEMrushService()

        wordpress_stats = wordpress_service.get_stats()
        semrush_stats = semrush_service.get_stats()

        return jsonify({
            'total_posts': wordpress_stats.get('total_posts', 0),
            'keywords_tracked': semrush_stats.get('total_keywords', 0),
            'monthly_traffic': semrush_stats.get('organic_traffic', 0),
            'conversions': semrush_stats.get('conversions', 0)
        })

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': str(e)}), 500