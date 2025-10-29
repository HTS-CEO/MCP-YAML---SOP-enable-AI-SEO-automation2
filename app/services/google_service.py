import requests
import os
from app.utils.logger import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta

class GoogleService:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
        self.ga4_property_id = os.getenv('GA4_PROPERTY_ID')
        self.gbp_account_id = os.getenv('GBP_ACCOUNT_ID')
        self.gbp_location_id = os.getenv('GBP_LOCATION_ID')
        self.logger = get_logger()

        # Setup session with retries
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _get_access_token(self):
        try:
            url = 'https://oauth2.googleapis.com/token'
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }

            response = self.session.post(url, data=data)
            response.raise_for_status()

            return response.json()['access_token']

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Google OAuth error: {str(e)}")
            raise Exception(f"Failed to get access token: {str(e)}")

    def create_gbp_post(self, post_data):
        try:
            access_token = self._get_access_token()
            url = f"https://mybusiness.googleapis.com/v4/accounts/{self.gbp_account_id}/locations/{self.gbp_location_id}/localPosts"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            data = {
                'summary': post_data['content'][:1500],  # GBP limit
                'callToAction': {
                    'actionType': 'LEARN_MORE',
                    'url': post_data.get('cta_url', '')
                } if post_data.get('cta_url') else None,
                'media': [{
                    'mediaFormat': 'PHOTO',
                    'sourceUrl': post_data['image_url']
                }] if post_data.get('image_url') else []
            }

            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}

            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"GBP post created: {result.get('name')}")
            return {
                'post_id': result.get('name'),
                'status': 'published'
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"GBP API error: {str(e)}")
            raise Exception(f"Failed to create GBP post: {str(e)}")

    def get_ga4_stats(self):
        try:
            access_token = self._get_access_token()
            url = f"https://analyticsdata.googleapis.com/v1beta/properties/{self.ga4_property_id}:runReport"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Get last 30 days data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            data = {
                'dateRanges': [{'startDate': start_date.isoformat(), 'endDate': end_date.isoformat()}],
                'dimensions': [{'name': 'date'}],
                'metrics': [
                    {'name': 'sessions'},
                    {'name': 'totalUsers'},
                    {'name': 'conversions'},
                    {'name': 'eventCount'}
                ]
            }

            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()

            result = response.json()
            rows = result.get('rows', [])

            # Aggregate data
            total_sessions = sum(int(row['metrics'][0]['values'][0]) for row in rows)
            total_users = sum(int(row['metrics'][1]['values'][0]) for row in rows)
            total_conversions = sum(int(row['metrics'][2]['values'][0]) for row in rows)

            return {
                'sessions': total_sessions,
                'users': total_users,
                'conversions': total_conversions,
                'period': '30_days'
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"GA4 API error: {str(e)}")
            return {
                'sessions': 0,
                'users': 0,
                'conversions': 0,
                'period': '30_days'
            }

    def get_gbp_stats(self):
        try:
            # Mock GBP stats - in real implementation would fetch from GBP API
            return {
                'total_posts': 25,
                'views': 1500,
                'clicks': 120,
                'engagement_rate': 8.0
            }

        except Exception as e:
            self.logger.error(f"GBP stats error: {str(e)}")
            return {
                'total_posts': 0,
                'views': 0,
                'clicks': 0,
                'engagement_rate': 0.0
            }