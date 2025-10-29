# Deployment Guide for SiteGround

## 🚀 SiteGround Cloud Deployment

This guide will help you deploy the AI-Powered SEO Automation System to SiteGround Cloud servers.

### Prerequisites

1. **SiteGround Cloud Account** with SSH access
2. **Domain/Subdomain** configured
3. **Python 3.13+** support (check with SiteGround)
4. **API Keys** for all required services

### Step 1: Upload Files

Upload all project files to your SiteGround hosting directory:

```bash
# Upload via FTP/SFTP to:
# public_html/ (for main domain)
# public_html/subdomain/ (for subdomain)
# OR
# home/yourusername/public_html/
```

### Step 2: Environment Configuration

1. **Create .env file** in your project root:
```bash
cp .env.example .env
```

2. **Edit .env** with your actual API keys:
```env
# Database Configuration
DATABASE_URL=sqlite:///seo_automation.db
SECRET_KEY=your-super-secret-key-change-this-in-production

# Environment
ENVIRONMENT=production

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@seoautomation.com

# WordPress Configuration
WP_BASE_URL=https://yoursite.com
WP_USER=your_username
WP_APP_PASSWORD=your_app_password

# SEMrush API
SEMRUSH_API_KEY=your_semrush_api_key

# OpenAI API
OPENAI_API_KEY=sk-your_openai_api_key

# Google APIs
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
GA4_PROPERTY_ID=your_property_id
GBP_ACCOUNT_ID=your_account_id
GBP_LOCATION_ID=your_location_id

# Authentication
AUTH_TOKEN=your_secure_api_token
JWT_SECRET_KEY=your-jwt-secret-key

# Slack Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### Step 3: Install Dependencies

```bash
# SSH into your SiteGround server
ssh yourusername@yourdomain.com

# Navigate to project directory
cd public_html

# Install Python dependencies
pip3 install -r requirements.txt

# If pip3 doesn't work, try:
python3 -m pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Initialize database
python3 main.py

# This will create the SQLite database and default admin user
```

### Step 5: Configure Passenger (WSGI)

Create a `passenger_wsgi.py` file in your project root:

```python
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variable for production
os.environ['ENVIRONMENT'] = 'production'

# Import the Flask app
from main import app as application
```

### Step 6: SiteGround Control Panel Configuration

1. **Login to SiteGround Control Panel**
2. **Go to "Websites" → "Site Tools"**
3. **Navigate to "Dev" → "Python"**
4. **Set Python version to 3.13+**
5. **Set Application Path** to your project directory
6. **Set WSGI File** to `passenger_wsgi.py`
7. **Set Entry Point** to `application`

### Step 7: File Permissions

```bash
# Set proper permissions
chmod 755 .
chmod 644 *.py
chmod 644 *.txt
chmod 644 *.md
chmod 600 .env
chmod 666 seo_automation.db
chmod -R 755 app/
chmod -R 755 templates/
chmod -R 755 logs/
```

### Step 8: Restart Application

1. **In SiteGround Control Panel:**
   - Go to "Dev" → "Python"
   - Click "Restart" button

2. **Or via SSH:**
```bash
# Kill any existing Python processes
pkill -f "python3 main.py"

# Restart the application (SiteGround will handle this)
```

### Step 9: Verify Deployment

1. **Check your domain/subdomain** - should show the landing page
2. **Test login functionality** - use admin/admin123
3. **Check API endpoints** - test with tools like Postman

### Troubleshooting 503 Errors

#### Common Causes:

1. **Missing Dependencies:**
```bash
# Check if all packages are installed
pip3 list | grep -E "(flask|openai|requests)"
```

2. **Environment Variables:**
```bash
# Verify .env file exists and has correct values
cat .env | head -10
```

3. **Database Issues:**
```bash
# Check database file
ls -la seo_automation.db

# Reinitialize if needed
rm seo_automation.db
python3 main.py
```

4. **WSGI Configuration:**
```bash
# Verify passenger_wsgi.py
cat passenger_wsgi.py
```

5. **File Permissions:**
```bash
# Check permissions
ls -la
ls -la app/
```

6. **Python Path Issues:**
```bash
# Check Python version
python3 --version

# Check if modules can be imported
python3 -c "import flask; print('Flask OK')"
```

#### SiteGround Specific Issues:

1. **Memory Limits:** SiteGround has memory limits - optimize your app
2. **Process Limits:** Only 2-3 worker processes allowed
3. **Timeout Issues:** Set appropriate timeouts in Gunicorn
4. **Database Locks:** SQLite might have locking issues under load

### Alternative Deployment Methods

#### Option 1: Use Gunicorn Directly
```bash
# Create start script
echo "gunicorn main:app --bind 127.0.0.1:8000 --workers 2 --threads 2 --timeout 30" > start.sh
chmod +x start.sh

# Run with nohup
nohup ./start.sh &
```

#### Option 2: Use Screen/Tmux
```bash
# Install screen
# Run app in screen session
screen -S seo_app
python3 main.py
# Detach with Ctrl+A+D
```

### Monitoring & Maintenance

1. **Check Logs:**
```bash
tail -f logs/seo_automation.log
```

2. **Monitor Processes:**
```bash
ps aux | grep python
```

3. **Restart Application:**
```bash
# Via control panel or
touch passenger_wsgi.py  # Triggers restart
```

### Performance Optimization

1. **Use Redis** for sessions in production
2. **Enable Gzip** compression
3. **Set up proper caching**
4. **Monitor memory usage**
5. **Use database connection pooling**

### Security Checklist

- ✅ `.env` file not in web-accessible directory
- ✅ Strong SECRET_KEY set
- ✅ Database file has restricted permissions
- ✅ Admin password changed from default
- ✅ API keys properly configured
- ✅ SSL certificate installed
- ✅ Regular backups configured

### Support

If you encounter issues:
1. Check SiteGround's Python documentation
2. Review application logs
3. Contact SiteGround support for hosting-specific issues
4. Check GitHub issues for known problems

---

**Note:** SiteGround's Python support may vary by plan. Ensure your hosting plan supports Python applications before deployment.