# AI-Powered SEO Automation System (Flask Version)

A comprehensive Flask-based API system that automates SEO tasks across WordPress, Google Business Profile, SEMrush, and Google Analytics 4. This system generates, optimizes, posts, and reports on content with minimal manual effort.

## 🚀 Features

### Core Functionality
- **AI Blog Generation**: Generate SEO-optimized blog posts (900–1200 words) with OpenAI
- **Content Re-optimization**: Monitor SEMrush rankings and re-optimize underperforming posts
- **Google Business Profile Management**: Automated posting with images and CTAs (100–150 words)
- **Analytics Integration**: Comprehensive reporting from SEMrush, GA4, and GBP
- **Background Automation**: Scheduled tasks for continuous optimization
- **RESTful API**: Token-based authentication with JSON responses

### Advanced Features
- **Multi-user Support**: Admin and user roles with separate dashboards
- **Database Storage**: SQLite with support for PostgreSQL migration
- **Error Handling**: Global exception handlers with Slack notifications
- **Retry Logic**: Exponential backoff for failed API calls
- **Logging**: Comprehensive logging with rotation and Slack alerts
- **Session Management**: JWT-based sessions with database persistence

## 📋 System Requirements

### Software Requirements
- **Python**: 3.8+
- **Flask**: 2.3.3+
- **Database**: SQLite (default) or PostgreSQL

### External Service Requirements
- **WordPress Site**: With REST API enabled and Application Passwords
- **SEMrush API**: Active API key for ranking data
- **OpenAI API**: API key for content generation
- **Google Cloud Project**: With My Business API and Analytics Data API enabled
- **Slack Webhook**: Optional for notifications

### Hardware Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for application, additional for logs and database
- **Network**: Stable internet connection for API calls

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-powered-seo-automation-flask
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

### 5. Initialize Database
```bash
python3 main.py
# Database tables will be created automatically on first run
```

## ⚙️ Configuration Guide

### Environment Variables (.env)

```env
# Database Configuration
DATABASE_URL=sqlite:///seo_automation.db
SECRET_KEY=your-super-secret-key-change-this-in-production

# Admin Credentials (Auto-created on first run)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@seoautomation.com

# WordPress Configuration
WP_BASE_URL=https://yourwordpresssite.com
WP_USER=your_username
WP_APP_PASSWORD=abcd efgh ijkl mnop

# SEMrush API
SEMRUSH_API_KEY=your_semrush_api_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Google APIs
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
GA4_PROPERTY_ID=your_ga4_property_id
GBP_ACCOUNT_ID=your_gbp_account_id
GBP_LOCATION_ID=your_gbp_location_id

# Authentication
AUTH_TOKEN=your_secure_api_token
JWT_SECRET_KEY=your-jwt-secret-key

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Optional: Redis for production (if using Celery)
REDIS_URL=redis://localhost:6379/0

# Session Configuration
SESSION_TYPE=filesystem
SESSION_PERMANENT=False
SESSION_KEY_PREFIX=seo_automation_

# Email Configuration (for user registration)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@seoautomation.com
```

### WordPress Setup
1. Install WordPress on your hosting
2. Enable REST API (usually enabled by default)
3. Create an Application Password in WordPress admin
4. Ensure the user has Editor or Administrator role

### Google API Setup
1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Required APIs**
   - Google My Business API
   - Google Analytics Data API
   - Google Analytics Admin API (if needed)

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Create "OAuth 2.0 Client IDs"
   - Download the JSON file

4. **Generate Refresh Token**
   - Use OAuth 2.0 Playground or custom script
   - Get refresh token for long-term access

### SEMrush API Setup
1. Sign up for SEMrush API access
2. Get your API key from account settings
3. Ensure sufficient API credits for your usage

### OpenAI API Setup
1. Create account at [OpenAI Platform](https://platform.openai.com/)
2. Generate API key
3. Add credits to your account
4. Monitor usage in dashboard

## 🚀 Usage Guide

### Starting the Application

#### Development Mode
```bash
python3 main.py
# Server starts on http://localhost:5000
```

#### Production Mode (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

#### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python3", "main.py"]
```

### Web Interface Access

#### Landing Page
- **URL**: `http://localhost:5000/`
- **Features**: Registration, login, feature overview

#### User Dashboard
- **URL**: `http://localhost:5000/dashboard`
- **Features**: Quick actions, stats overview, recent activity

#### Admin Panel
- **URL**: `http://localhost:5000/admin`
- **Features**: User management, API configuration guide, system logs

#### API Configuration
- **URL**: `http://localhost:5000/admin/api-keys`
- **Features**: Environment configuration guide, .env template download, setup instructions
- **Note**: API keys are now managed exclusively through the `.env` file for enhanced security

### API Endpoints Documentation

#### Authentication
All API endpoints require Bearer token authentication:
```
Authorization: Bearer your_auth_token
```

#### 1. Generate Blog Post
**Endpoint**: `POST /api/generate_blog`
**Purpose**: Generate SEO-optimized blog post using AI

**Request**:
```json
{
  "keyword": "best SEO tools 2025",
  "secondary_keywords": "SEO software, ranking tools"
}
```

**Response**:
```json
{
  "post_id": 123,
  "title": "Complete Guide to Best SEO Tools 2025",
  "status": "draft"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/generate_blog \
  -H "Authorization: Bearer your_auth_token" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "best SEO tools 2025", "secondary_keywords": "SEO software"}'
```

#### 2. Re-optimize Content
**Endpoint**: `POST /api/reoptimize`
**Purpose**: Re-optimize existing post based on ranking performance

**Request**:
```json
{
  "post_id": 123,
  "keywords": "target keywords"
}
```

**Response**:
```json
{
  "post_id": 123,
  "ranking_change": "Optimized for better ranking (was position 15)",
  "message": "Post re-optimized successfully"
}
```

#### 3. Create GBP Post
**Endpoint**: `POST /api/gbp_post`
**Purpose**: Publish condensed content to Google Business Profile

**Request**:
```json
{
  "content": "Check out our latest SEO services! We help businesses improve their online visibility with cutting-edge strategies.",
  "image_url": "https://example.com/image.jpg",
  "cta_url": "https://yourwebsite.com/contact"
}
```

**Response**:
```json
{
  "post_id": "accounts/123/locations/456/posts/789",
  "status": "published",
  "message": "Successfully published to Google Business Profile"
}
```

#### 4. Generate Analytics Report
**Endpoint**: `GET /api/report`
**Purpose**: Aggregate data from all services into comprehensive report

**Response**:
```json
{
  "generated_at": "2025-01-15T10:30:00Z",
  "wordpress": {
    "total_posts": 45,
    "published_posts": 42
  },
  "semrush": {
    "total_keywords": 150,
    "organic_traffic": 25000,
    "average_position": 12.5,
    "conversions": 1250
  },
  "ga4": {
    "sessions": 15420,
    "users": 8920,
    "conversions": 234,
    "period": "30_days"
  },
  "gbp": {
    "total_posts": 25,
    "views": 1500,
    "clicks": 120,
    "engagement_rate": 8.0
  },
  "summary": {
    "total_traffic": 40420,
    "total_conversions": 1484,
    "content_created": 70,
    "seo_performance_score": 78
  }
}
```

#### 5. Dashboard Stats
**Endpoint**: `GET /api/dashboard_stats`
**Purpose**: Get simplified stats for dashboard display

**Response**:
```json
{
  "total_posts": 45,
  "keywords_tracked": 150,
  "monthly_traffic": 25000,
  "conversions": 1250
}
```

## 📊 Automated Tasks & Scheduling

The system includes background automation powered by APScheduler:

### Daily Tasks (9:00 AM)
- **SEMrush Ranking Check**: Monitor keyword positions
- **Content Re-optimization**: Automatically improve underperforming posts
- **Health Monitoring**: Check API connectivity and system status

### Weekly Tasks (Monday 10:00 AM)
- **GBP Photo Upload**: Post images and content to Google Business Profile
- **Content Generation**: Generate new blog post ideas
- **Performance Reports**: Weekly summary reports

### Monthly Tasks (1st of month 8:00 AM)
- **Comprehensive Reports**: Full analytics aggregation
- **Backup Creation**: Database and configuration backups
- **Performance Analysis**: Monthly SEO performance review

### Manual Triggers
All automated tasks can also be triggered manually via API endpoints or web interface.

## 🏗️ Project Architecture

### Directory Structure
```
ai-powered-seo-automation-flask/
├── app/
│   ├── models.py              # Database models and managers
│   ├── routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── blog.py            # Blog generation API
│   │   ├── reoptimize.py      # Content optimization API
│   │   ├── gbp.py            # Google Business Profile API
│   │   └── report.py         # Analytics reporting API
│   ├── services/
│   │   ├── wordpress_service.py    # WordPress API integration
│   │   ├── semrush_service.py      # SEMrush API integration
│   │   ├── google_service.py       # Google APIs integration
│   │   ├── openai_service.py       # OpenAI API integration
│   │   └── report_service.py       # Report generation logic
│   └── utils/
│       ├── auth.py            # Authentication decorators
│       └── logger.py          # Logging and notifications
├── templates/                 # HTML templates
│   ├── landing.html          # Landing page
│   ├── dashboard.html        # User dashboard
│   ├── admin_dashboard.html  # Admin panel
│   └── ...                   # Other templates
├── logs/                     # Application logs
├── flask_session/            # Session storage
├── main.py                   # Flask application entry point
├── scheduler.py              # Background task scheduler
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration
├── seo_automation.db         # SQLite database
└── README.md                 # This documentation
```

### Key Components

#### Models Layer (`app/models.py`)
- **DatabaseManager**: Handles database connections and initialization
- **UserManager**: User authentication and management
- **APIKeyManager**: API key storage and management
- **SessionManager**: JWT session handling

#### Routes Layer (`app/routes/`)
- **auth.py**: User authentication, registration, and session management
- **blog.py**: Blog post generation endpoints
- **reoptimize.py**: Content optimization endpoints
- **gbp.py**: Google Business Profile management
- **report.py**: Analytics and reporting

#### Services Layer (`app/services/`)
- **wordpress_service.py**: WordPress REST API integration
- **semrush_service.py**: SEMrush API client with retry logic
- **google_service.py**: Google APIs (GBP, GA4) integration
- **openai_service.py**: OpenAI content generation
- **report_service.py**: Data aggregation and report generation

#### Utils Layer (`app/utils/`)
- **auth.py**: Authentication decorators and validation
- **logger.py**: Centralized logging with Slack notifications

## 🔒 Security Features

### Authentication & Authorization
- **Token-based API Authentication**: Bearer tokens for API access
- **Session Management**: JWT-based web sessions with database persistence
- **Role-based Access Control**: Admin and user roles with different permissions
- **Password Security**: bcrypt hashing for password storage

### Data Protection
- **Input Validation**: pydantic models for request validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Template escaping and sanitization
- **CSRF Protection**: Flask-WTF for form security
- **Environment Variables**: Sensitive API keys stored securely in .env files

### API Security
- **Rate Limiting**: Request throttling to prevent abuse
- **Error Handling**: Generic error messages to prevent information leakage
- **Logging**: Comprehensive audit logging
- **Environment Variables**: Sensitive data stored securely

## 📈 Monitoring & Logging

### Logging System
- **File Logging**: Rotating log files in `logs/` directory
- **Console Logging**: Real-time logging to console
- **Slack Notifications**: Error alerts and important events
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Monitoring Features
- **Health Checks**: Automated system health monitoring
- **Performance Metrics**: Response times and API call tracking
- **Error Tracking**: Detailed error logging with stack traces
- **Usage Analytics**: API usage statistics and trends

### Log Files
- `logs/seo_automation.log`: Main application log
- Database logs: SQLite query logging
- API logs: External API call logs

## 🚀 Deployment Options

### Development Deployment
```bash
# Simple development server
python3 main.py
```

### Production Deployment (Gunicorn)
```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
```

### Cloud Deployment Options
- **Heroku**: Direct deployment with Procfile
- **AWS**: EC2, ECS, or Elastic Beanstalk
- **Google Cloud**: App Engine or Compute Engine
- **DigitalOcean**: App Platform or Droplets
- **Railway**: Direct Git integration

### SiteGround Deployment
```bash
# For SiteGround shared hosting
# 1. Upload files to public_html or subdomain directory
# 2. Set up Python application in cPanel
# 3. Configure Passenger or FastCGI
# 4. Set environment variables in .htaccess or control panel
```

## 🧪 Testing & Quality Assurance

### Running Tests
```bash
# Install test dependencies
pip install pytest flask-testing pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure
```
tests/
├── test_auth.py          # Authentication tests
├── test_blog.py          # Blog generation tests
├── test_services.py      # Service layer tests
├── test_api.py           # API endpoint tests
└── conftest.py           # Test configuration
```

### Test Coverage
- Unit tests for all service methods
- Integration tests for API endpoints
- Authentication and authorization tests
- Database operation tests
- External API mocking tests

## 📝 API Reference

### HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "error": "Error message description",
  "details": "Additional error information (optional)",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Pagination
For list endpoints, pagination is supported:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

## 🤝 Contributing Guidelines

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Set up development environment
4. Make your changes
5. Write tests for new features
6. Ensure all tests pass
7. Update documentation if needed
8. Submit a pull request

### Code Standards
- **PEP 8**: Python style guide compliance
- **Type Hints**: Use type annotations where possible
- **Docstrings**: Comprehensive function documentation
- **Error Handling**: Proper exception handling and logging
- **Security**: Follow security best practices

### Testing Requirements
- Minimum 80% test coverage
- All new features must have tests
- Integration tests for API changes
- Documentation updates for API changes

## 📄 License & Legal

### License
This project is licensed under the MIT License - see the LICENSE file for details.

### Third-party Licenses
- Flask: BSD License
- OpenAI: MIT License
- APScheduler: MIT License
- Other dependencies: Refer to individual package licenses

## 🆘 Support & Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database file permissions
ls -la seo_automation.db

# Reinitialize database
rm seo_automation.db
python3 main.py
```

#### API Key Issues
- Verify API keys in `.env` file
- Check API key permissions and quotas
- Review API documentation for rate limits

#### WordPress Connection Issues
- Ensure WordPress REST API is enabled
- Verify Application Password is correct
- Check WordPress user permissions

### Getting Help
1. **Check Logs**: Review `logs/seo_automation.log`
2. **API Documentation**: Refer to this README
3. **GitHub Issues**: Open an issue for bugs
4. **Community Support**: Check discussions section

### Performance Optimization
- Use database indexes for large datasets
- Implement caching for frequent API calls
- Monitor memory usage and optimize queries
- Use connection pooling for database connections

## 🔄 Version History & Changelog

### Version 1.0.0 (Current)
- ✅ Initial release with core SEO automation features
- ✅ Comprehensive API for WordPress, SEMrush, GBP, and GA4 integration
- ✅ Background scheduling and automated optimization
- ✅ Web dashboard for monitoring and manual operations
- ✅ Multi-user support with admin and user roles
- ✅ Database storage with SQLite backend
- ✅ Comprehensive logging and error handling
- ✅ Slack notifications for system events
- ✅ Token-based API authentication
- ✅ Session management with JWT tokens
- ✅ Input validation and security measures

### Planned Features (Future Versions)
- 🔄 PostgreSQL support for production deployments
- 🔄 Redis caching layer for improved performance
- 🔄 Advanced analytics dashboard with charts
- 🔄 Multi-language content generation
- 🔄 A/B testing for content optimization
- 🔄 Social media integration beyond GBP
- 🔄 Advanced reporting with PDF export
- 🔄 API rate limiting and throttling
- 🔄 Backup and restore functionality
- 🔄 Docker containerization improvements

---

**Built with ❤️ for SEO professionals and digital marketers**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/your-repo/ai-powered-seo-automation-flask).