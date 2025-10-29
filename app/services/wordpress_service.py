import requests
import os
from app.utils.logger import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class WordPressService:
    def __init__(self):
        self.base_url = os.getenv('WP_BASE_URL')
        self.username = os.getenv('WP_USER')
        self.app_password = os.getenv('WP_APP_PASSWORD')
        self.logger = get_logger()

        # Setup session with retries
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _get_auth_headers(self):
        import base64
        credentials = f"{self.username}:{self.app_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded_credentials}'}

    def create_post(self, post_data):
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            headers = self._get_auth_headers()
            headers['Content-Type'] = 'application/json'

            # Prepare post data
            data = {
                'title': post_data['title'],
                'content': post_data['content'],
                'status': post_data.get('status', 'draft'),
                'meta': post_data.get('meta', {})
            }

            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()

            self.logger.info(f"WordPress post created: {response.json().get('id')}")
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WordPress API error: {str(e)}")
            raise Exception(f"Failed to create WordPress post: {str(e)}")

    def get_post(self, post_id):
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            headers = self._get_auth_headers()

            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WordPress API error: {str(e)}")
            raise Exception(f"Failed to get WordPress post: {str(e)}")

    def update_post(self, post_id, post_data):
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            headers = self._get_auth_headers()
            headers['Content-Type'] = 'application/json'

            data = {
                'title': post_data.get('title'),
                'content': post_data.get('content'),
                'meta': post_data.get('meta', {})
            }

            response = self.session.put(url, json=data, headers=headers)
            response.raise_for_status()

            self.logger.info(f"WordPress post updated: {post_id}")
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WordPress API error: {str(e)}")
            raise Exception(f"Failed to update WordPress post: {str(e)}")

    def upload_media(self, file_path, alt_text=''):
        try:
            url = f"{self.base_url}/wp-json/wp/v2/media"
            headers = self._get_auth_headers()

            with open(file_path, 'rb') as file:
                files = {'file': file}
                data = {'alt_text': alt_text} if alt_text else {}

                response = self.session.post(url, files=files, data=data, headers=headers)
                response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WordPress media upload error: {str(e)}")
            raise Exception(f"Failed to upload media: {str(e)}")

    def get_stats(self):
        try:
            # Get total posts count
            url = f"{self.base_url}/wp-json/wp/v2/posts?per_page=1"
            headers = self._get_auth_headers()

            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            total_posts = int(response.headers.get('X-WP-Total', 0))

            return {
                'total_posts': total_posts,
                'published_posts': total_posts  # Simplified
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WordPress stats error: {str(e)}")
            return {'total_posts': 0, 'published_posts': 0}