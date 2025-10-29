import pytest
from unittest.mock import Mock, patch
from app.services.wordpress_service import WordPressService
from app.services.openai_service import OpenAIService
from app.services.report_service import ReportService


class TestWordPressService:
    """Test WordPress service functionality"""

    @patch('app.services.wordpress_service.requests.Session')
    def test_create_post_success(self, mock_session):
        """Test successful post creation"""
        # Mock the session and response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 123, 'title': {'rendered': 'Test Post'}}

        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = WordPressService()
        result = service.create_post({
            'title': 'Test Post',
            'content': 'Test content',
            'status': 'draft'
        })

        assert result['id'] == 123
        mock_session_instance.post.assert_called_once()

    @patch('app.services.wordpress_service.requests.Session')
    def test_create_post_failure(self, mock_session):
        """Test post creation failure"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")

        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = WordPressService()

        with pytest.raises(Exception):
            service.create_post({
                'title': 'Test Post',
                'content': 'Test content'
            })


class TestOpenAIService:
    """Test OpenAI service functionality"""

    @patch('app.services.openai_service.openai.ChatCompletion.create')
    def test_generate_blog_post_success(self, mock_create):
        """Test successful blog post generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"title": "Test Title", "content": "Test content", "seo_title": "SEO Title", "seo_description": "SEO Description", "faq": "FAQ content"}'
        mock_create.return_value = mock_response

        service = OpenAIService()
        result = service.generate_blog_post("test keyword")

        assert result['title'] == "Test Title"
        assert result['content'] == "Test content"
        mock_create.assert_called_once()

    @patch('app.services.openai_service.openai.ChatCompletion.create')
    def test_generate_blog_post_failure(self, mock_create):
        """Test blog post generation failure"""
        mock_create.side_effect = Exception("OpenAI API Error")

        service = OpenAIService()
        result = service.generate_blog_post("test keyword")

        # Should return fallback content
        assert 'title' in result
        assert 'content' in result
        assert 'Complete Guide to test keyword' in result['title']


class TestReportService:
    """Test report service functionality"""

    def test_generate_report_success(self):
        """Test successful report generation"""
        service = ReportService()

        test_data = {
            'wordpress': {'total_posts': 10, 'published_posts': 8},
            'semrush': {'total_keywords': 50, 'organic_traffic': 10000, 'average_position': 15.5, 'conversions': 500},
            'ga4': {'sessions': 5000, 'users': 3000, 'conversions': 100, 'period': '30_days'},
            'gbp': {'total_posts': 5, 'views': 1000, 'clicks': 50, 'engagement_rate': 5.0}
        }

        result = service.generate_report(test_data)

        assert 'generated_at' in result
        assert result['wordpress']['total_posts'] == 10
        assert result['semrush']['total_keywords'] == 50
        assert 'summary' in result
        assert 'seo_performance_score' in result['summary']

    def test_calculate_seo_score(self):
        """Test SEO score calculation"""
        service = ReportService()

        semrush_data = {'average_position': 10, 'organic_traffic': 20000}
        wordpress_data = {'total_posts': 20}

        score = service._calculate_seo_score(semrush_data, wordpress_data)

        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, int)

    def test_export_to_json(self, tmp_path):
        """Test JSON export functionality"""
        service = ReportService()

        test_report = {
            'generated_at': '2025-01-01T00:00:00Z',
            'wordpress': {'total_posts': 5}
        }

        filename = service.export_to_json(test_report, str(tmp_path / 'test_report.json'))

        assert (tmp_path / 'test_report.json').exists()

        # Verify content
        import json
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
            assert loaded_data['wordpress']['total_posts'] == 5