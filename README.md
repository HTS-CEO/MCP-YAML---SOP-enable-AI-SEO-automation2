# AI-Powered SEO Automation System

A comprehensive web application that automates SEO tasks across WordPress, Google Business Profile, SEMrush, and Google Analytics 4. Generate SEO-optimized blog posts, monitor rankings, create social media content, and get detailed analytics reports - all with minimal manual effort.

## 🚀 Features

### Core Functionality
- **AI Blog Generation**: Create SEO-optimized blog posts (900–1200 words) using OpenAI
- **Content Re-optimization**: Monitor SEMrush rankings and automatically improve underperforming posts
- **Google Business Profile Management**: Automated posting with images and CTAs (100–150 words)
- **Analytics Integration**: Comprehensive reporting from SEMrush, GA4, and GBP
- **Background Automation**: Scheduled tasks for continuous optimization
- **Web Dashboard**: User-friendly interface for all operations

### Advanced Features
- **User Authentication**: Secure login/registration system
- **Real-time API Status**: Check connection status for all integrated services
- **Automated Notifications**: Slack and email alerts for important events
- **Database Storage**: SQLite with PostgreSQL support
- **Comprehensive Logging**: Detailed activity tracking and error monitoring
- **Background Automation**: Scheduled tasks for continuous optimization

## 🔑 Required API Keys & Setup

### 1. OpenAI API Key
**Needed for**: AI content generation and optimization
- Go to [OpenAI Platform](https://platform.openai.com/)
- Sign up/Login to your account
- Navigate to API Keys section
- Click "Create new secret key"
- Copy the key (starts with `sk-`)

### 2. WordPress Setup
**Needed for**: Blog post publishing
- Install WordPress on your hosting
- Go to WordPress Admin → Users → Your Profile
- Scroll to "Application Passwords" section
- Enter a name (e.g., "SEO Automation") and click "Add New"
- Copy the generated application password
- **Required Info**:
  - WordPress Site URL (e.g., `https://yourblog.com`)
  - WordPress Username
  - Application Password

### 3. SEMrush API Key
**Needed for**: Keyword ranking monitoring
- Go to [SEMrush API](https://www.semrush.com/api/)
- Sign up for API access
- Get your API key from account settings
- Ensure sufficient API credits

### 4. Google APIs Setup
**Needed for**: Google Business Profile and Analytics

#### Step 1: Create Google Cloud Project
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select existing one

#### Step 2: Enable Required APIs
- Search for and enable:
  - "Google My Business API"
  - "Google Analytics Data API"
  - "Google Analytics Admin API"

#### Step 3: Create OAuth 2.0 Credentials
- Go to "APIs & Services" → "Credentials"
- Click "Create Credentials" → "OAuth 2.0 Client IDs"
- Configure OAuth consent screen if prompted
- Download the JSON file

#### Step 4: Get Refresh Token
- Use [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- Select required scopes (My Business, Analytics)
- Exchange authorization code for refresh token
- **Required Info**:
  - Client ID
  - Client Secret
  - Refresh Token
  - GA4 Property ID (from Google Analytics)
  - GBP Account ID and Location ID (from Google My Business)

### 5. Slack Webhook (Optional)
**Needed for**: Automated notifications
- Go to [Slack Apps](https://api.slack.com/apps)
- Create new app → "From scratch"
- Add "Incoming Webhooks" feature
- Create webhook URL for your channel
- Copy the webhook URL

## ⚙️ Configuration

### Environment Variables Setup

#### For Local Development (.env file)
Create a `.env` file in your project root with:

```env
# Database
DATABASE_URL=sqlite:///seo_automation.db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# WordPress
WP_BASE_URL=https://yourwordpresssite.com
WP_USER=your_username
WP_APP_PASSWORD=abcd-efgh-ijkl-mnop

# SEMrush
SEMRUSH_API_KEY=your-semrush-api-key

# Google APIs
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token
GA4_PROPERTY_ID=GA_MEASUREMENT_ID
GBP_ACCOUNT_ID=your-gbp-account-id
GBP_LOCATION_ID=your-gbp-location-id

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Session Configuration
SESSION_TYPE=filesystem
SESSION_KEY_PREFIX=seo_automation_
```

#### For Render Deployment
When deploying to Render, set environment variables in your Render dashboard:

1. **Go to your Render service dashboard**
2. **Navigate to Environment**
3. **Add the following environment variables:**

```
# Database
DATABASE_URL=postgresql://your-render-postgres-url
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# WordPress
WP_BASE_URL=https://yourwordpresssite.com
WP_USER=your_username
WP_APP_PASSWORD=abcd-efgh-ijkl-mnop

# SEMrush
SEMRUSH_API_KEY=your-semrush-api-key

# Google APIs
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token
GA4_PROPERTY_ID=GA_MEASUREMENT_ID
GBP_ACCOUNT_ID=your-gbp-account-id
GBP_LOCATION_ID=your-gbp-location-id

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Render Specific
RENDER=true
ENVIRONMENT=production
PYTHON_VERSION=3.9.7
```

**Note**: For Render, use PostgreSQL instead of SQLite. Create a PostgreSQL database in Render and use its connection string for `DATABASE_URL`.

## 🚀 Getting Started

### First Time Setup
1. **Start the Application**
   ```bash
   python main.py
   ```
   Server starts on `http://localhost:5000`

2. **Create Admin Account**
   - Visit `http://localhost:5000`
   - Click "Get Started" → Register
   - Create your admin account

3. **Configure API Keys**
   - Login to dashboard
   - Go to Settings (`/settings`)
   - Enter all your API keys in the API Configuration section
   - Click "Check API Status" to verify connections
   - Save settings

## 📱 User Interface Guide

### Dashboard (`/dashboard`)
- **Overview**: Welcome message, user info, and quick stats
- **Quick Actions**: Direct links to main features
- **Statistics**: Total posts, keywords tracked, traffic, conversions
- **Recent Activity**: Timeline of recent actions

### Generate Blog Posts (`/blog`)
1. Enter target keyword (required)
2. Add secondary keywords (optional)
3. Select target audience and tone
4. Click "Generate Blog Post"
5. Wait for AI generation (shows loading spinner)
6. Post is created as draft in WordPress
7. Check Recent Posts section for status

### Settings (`/settings`)
- **API Configuration**: Enter and manage all API keys
- **API Status**: Real-time connection status for each service
- **Automation Settings**: Toggle automated features
- **Notifications**: Configure Slack and email alerts
- **System Settings**: Database backup, logging, rate limits

### Other Pages
- **Re-optimize Posts** (`/reoptimize`): Improve existing content based on ranking performance
- **Google Business** (`/gbp`): Create and publish posts to Google Business Profile
- **Analytics** (`/analytics`): View detailed analytics from Google Analytics 4
- **Reports** (`/reports`): Comprehensive performance reports combining all data sources

## 🔄 Daily Workflow

### Morning Routine (15 minutes)
1. **Check Dashboard**: Review overnight stats and activity
2. **Generate Content**: Create 1-2 new blog posts using AI
3. **Monitor Rankings**: System automatically checks keyword positions
4. **Review Notifications**: Check for any alerts or issues

### Afternoon Tasks (10 minutes)
1. **Publish Content**: Review and publish draft posts in WordPress
2. **Create Social Posts**: Generate Google Business Profile content
3. **Check API Status**: Ensure all services are connected

### Weekly Tasks (30 minutes)
1. **Review Reports**: Check comprehensive analytics
2. **Optimize Content**: Re-run underperforming posts through AI
3. **Update Keywords**: Add new target keywords to track
4. **Clean Up**: Archive old drafts and update settings

## 📊 Understanding the Features

### AI Blog Generation
- **Input**: Primary keyword + optional secondary keywords
- **Output**: Complete 900-1200 word SEO-optimized article
- **Features**: Automatic meta descriptions, title optimization, internal linking suggestions
- **Publishing**: Posts created as drafts in WordPress for review

### Content Re-optimization
- **Trigger**: Posts ranking below configurable threshold (default: position 20)
- **Process**: AI analyzes existing content and creates improved versions
- **Output**: Updated WordPress posts with better SEO optimization
- **Automation**: Runs daily automatically based on SEMrush ranking data

### Google Business Profile
- **Content Limit**: 1500 characters maximum
- **Features**: Image support, call-to-action buttons
- **Posting**: Direct publishing to your GBP listing
- **Analytics**: Track views, clicks, and engagement

### Analytics & Reporting
- **Data Sources**: WordPress, SEMrush, Google Analytics 4, Google Business Profile
- **Reports**: Daily rankings, traffic analysis, conversion tracking
- **Export**: Data available for external analysis

## 🔧 Troubleshooting

### Common Issues

#### "Database not configured" Error
- Check your `.env` file exists and has correct `DATABASE_URL`
- Ensure SQLite file permissions are correct
- Try restarting the application

#### API Connection Failed
- Verify API keys are entered correctly in Settings
- Check API key permissions and quotas
- Use "Check API Status" button to test connections
- Review API documentation for rate limits

#### WordPress Publishing Issues
- Ensure WordPress REST API is enabled
- Verify Application Password is correct
- Check user has Editor/Administrator permissions
- Confirm WordPress URL is accessible

#### OpenAI Generation Errors
- Check API key is valid and has credits
- Verify OpenAI account has sufficient usage allowance
- Try with simpler keywords if complex ones fail

#### Google API Issues
- Ensure all required APIs are enabled in Google Cloud
- Verify OAuth credentials are correct
- Check refresh token is valid (may need renewal)
- Confirm GBP account/location IDs are accurate

### Getting Help
1. **Check Logs**: Review application logs for detailed error messages
2. **API Status**: Use Settings page to check service connections
3. **Dashboard**: Monitor recent activity for clues
4. **Notifications**: Check Slack/email for system alerts

## 📈 Performance Optimization

### API Usage Tips
- Monitor OpenAI costs in their dashboard
- Check SEMrush API credits regularly
- Set appropriate rate limits in settings
- Use automation sparingly to avoid API limits

### Content Strategy
- Focus on high-value keywords with good search volume
- Maintain consistent posting schedule
- Monitor ranking improvements over time
- Use analytics to identify top-performing content

### System Maintenance
- Regular database backups (enabled by default)
- Monitor log file sizes and retention
- Keep dependencies updated
- Review and optimize settings quarterly

## 🔒 Security Best Practices

### API Key Management
- Never share API keys publicly
- Rotate keys regularly
- Use environment variables (not hardcoded)
- Monitor API usage for unauthorized access

### User Access
- Use strong passwords
- Enable two-factor authentication if available
- Regularly review user permissions
- Log out after use

### Data Protection
- Regular database backups
- Secure file permissions
- Monitor for suspicious activity
- Keep system updated

---

**Built for SEO professionals and digital marketers who want to automate their content workflow while maintaining quality and performance.**

*Last updated: January 2025*
