import requests
import os
from app.utils.logger import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SEMrushService:
    def __init__(self):
        self.api_key = os.getenv('SEMRUSH_API_KEY')
        self.base_url = 'https://api.semrush.com'
        self.logger = get_logger()

        # Setup session with retries
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get_keyword_ranking(self, keyword, database='us'):
        try:
            url = f"{self.base_url}/analytics/keywordoverview"
            params = {
                'key': self.api_key,
                'keyword': keyword,
                'database': database,
                'export_columns': 'Ph,Po,Pp,Pd,Nq,Cp,Co,Nr,Td'
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    'keyword': keyword,
                    'position': int(result.get('Po', 0)),
                    'previous_position': int(result.get('Pp', 0)),
                    'search_volume': int(result.get('Nq', 0)),
                    'competition': result.get('Co', 'N/A'),
                    'cpc': float(result.get('Cp', 0))
                }

            return {'keyword': keyword, 'position': 0, 'error': 'No data found'}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"SEMrush API error: {str(e)}")
            return {'keyword': keyword, 'position': 0, 'error': str(e)}

    def get_domain_organic_keywords(self, domain, database='us', limit=100):
        try:
            url = f"{self.base_url}/analytics/organic"
            params = {
                'key': self.api_key,
                'domain': domain,
                'database': database,
                'display_limit': limit,
                'export_columns': 'Ph,Po,Nq,Cp,Co'
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            keywords = []
            for item in data:
                keywords.append({
                    'keyword': item.get('Ph'),
                    'position': int(item.get('Po', 0)),
                    'search_volume': int(item.get('Nq', 0)),
                    'cpc': float(item.get('Cp', 0)),
                    'competition': item.get('Co')
                })

            return keywords

        except requests.exceptions.RequestException as e:
            self.logger.error(f"SEMrush organic keywords error: {str(e)}")
            return []

    def get_stats(self):
        try:
            # Mock stats for demonstration - in real implementation,
            # this would aggregate data from multiple keyword queries
            return {
                'total_keywords': 150,
                'organic_traffic': 25000,
                'average_position': 12.5,
                'conversions': 1250
            }

        except Exception as e:
            self.logger.error(f"SEMrush stats error: {str(e)}")
            return {
                'total_keywords': 0,
                'organic_traffic': 0,
                'average_position': 0,
                'conversions': 0
            }