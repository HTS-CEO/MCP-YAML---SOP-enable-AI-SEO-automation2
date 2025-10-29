from app.utils.logger import get_logger
import json
from datetime import datetime

class ReportService:
    def __init__(self):
        self.logger = get_logger()

    def generate_report(self, data):
        try:
            wordpress = data.get('wordpress', {})
            semrush = data.get('semrush', {})
            ga4 = data.get('ga4', {})
            gbp = data.get('gbp', {})

            report = {
                'generated_at': datetime.now().isoformat(),
                'wordpress': {
                    'total_posts': wordpress.get('total_posts', 0),
                    'published_posts': wordpress.get('published_posts', 0)
                },
                'semrush': {
                    'total_keywords': semrush.get('total_keywords', 0),
                    'organic_traffic': semrush.get('organic_traffic', 0),
                    'average_position': semrush.get('average_position', 0),
                    'conversions': semrush.get('conversions', 0)
                },
                'ga4': {
                    'sessions': ga4.get('sessions', 0),
                    'users': ga4.get('users', 0),
                    'conversions': ga4.get('conversions', 0),
                    'period': ga4.get('period', '30_days')
                },
                'gbp': {
                    'total_posts': gbp.get('total_posts', 0),
                    'views': gbp.get('views', 0),
                    'clicks': gbp.get('clicks', 0),
                    'engagement_rate': gbp.get('engagement_rate', 0)
                },
                'summary': {
                    'total_traffic': semrush.get('organic_traffic', 0) + ga4.get('sessions', 0),
                    'total_conversions': semrush.get('conversions', 0) + ga4.get('conversions', 0),
                    'content_created': wordpress.get('total_posts', 0) + gbp.get('total_posts', 0),
                    'seo_performance_score': self._calculate_seo_score(semrush, wordpress)
                }
            }

            self.logger.info("Comprehensive report generated")
            return report

        except Exception as e:
            self.logger.error(f"Report generation error: {str(e)}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def _calculate_seo_score(self, semrush, wordpress):
        try:
            # Simple SEO score calculation
            position_score = max(0, 100 - (semrush.get('average_position', 50) * 2))
            content_score = min(100, wordpress.get('total_posts', 0) * 2)
            traffic_score = min(100, semrush.get('organic_traffic', 0) / 1000)

            return int((position_score + content_score + traffic_score) / 3)

        except Exception as e:
            self.logger.error(f"SEO score calculation error: {str(e)}")
            return 0

    def export_to_json(self, report_data, filename=None):
        try:
            if not filename:
                filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)

            self.logger.info(f"Report exported to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Report export error: {str(e)}")
            raise Exception(f"Failed to export report: {str(e)}")

    def create_backup(self, data, client_name):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backups/{client_name}/{timestamp}.json"

            # Ensure directory exists
            import os
            os.makedirs(f"backups/{client_name}", exist_ok=True)

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Backup created: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Backup creation error: {str(e)}")
            raise Exception(f"Failed to create backup: {str(e)}")