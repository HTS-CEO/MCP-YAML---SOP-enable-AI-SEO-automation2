from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.semrush_service import SEMrushService
from app.services.wordpress_service import WordPressService
from app.services.google_service import GoogleService
from app.services.openai_service import OpenAIService
from app.services.report_service import ReportService
from app.utils.logger import get_logger
import sqlite3
from datetime import datetime

logger = get_logger()

def check_keyword_rankings():
    """Daily SEMrush ranking check and re-optimization trigger"""
    try:
        logger.info("Starting daily keyword ranking check")

        semrush_service = SEMrushService()
        wordpress_service = WordPressService()
        openai_service = OpenAIService()

        # Get posts that need checking
        conn = sqlite3.connect('seo_automation.db')
        c = conn.cursor()
        c.execute('''SELECT id, wordpress_id, keywords FROM posts
                     WHERE created_at >= date('now', '-30 days')''')
        posts = c.fetchall()
        conn.close()

        reoptimized_count = 0
        for post in posts:
            post_id, wp_id, keywords = post
            if keywords:
                # Check ranking for primary keyword
                primary_keyword = keywords.split(',')[0].strip()
                ranking = semrush_service.get_keyword_ranking(primary_keyword)

                if ranking.get('position', 100) > 20:  # If not in top 20
                    # Re-optimize the post
                    existing_post = wordpress_service.get_post(wp_id)
                    optimized = openai_service.reoptimize_content(
                        existing_post['content'],
                        keywords
                    )

                    wordpress_service.update_post(wp_id, {
                        'content': optimized['content'],
                        'meta': {
                            'seo_title': optimized['seo_title'],
                            'seo_description': optimized['seo_description']
                        }
                    })

                    reoptimized_count += 1
                    logger.info(f"Re-optimized post {wp_id} for keyword: {primary_keyword}")

        logger.info(f"Daily ranking check completed. Re-optimized {reoptimized_count} posts")

    except Exception as e:
        logger.error(f"Error in daily ranking check: {str(e)}")

def upload_weekly_gbp_photos():
    """Weekly Google Business Profile photo upload"""
    try:
        logger.info("Starting weekly GBP photo upload")

        google_service = GoogleService()
        openai_service = OpenAIService()

        # Generate content for GBP post with image
        topics = [
            "Our latest services",
            "Customer success stories",
            "Behind the scenes",
            "Industry insights",
            "Special offers"
        ]

        for topic in topics[:3]:  # Upload 3 posts per week
            content = openai_service.generate_gbp_content(topic, 100)

            # In a real implementation, you'd have a pool of images
            # For now, we'll skip the image upload
            post_data = {
                'content': content,
                'image_url': None,  # Would be a pre-uploaded image URL
                'cta_url': 'https://yourwebsite.com'
            }

            google_service.create_gbp_post(post_data)
            logger.info(f"Created weekly GBP post: {topic}")

        logger.info("Weekly GBP photo upload completed")

    except Exception as e:
        logger.error(f"Error in weekly GBP upload: {str(e)}")

def generate_monthly_report():
    """Monthly comprehensive report generation"""
    try:
        logger.info("Starting monthly report generation")

        wordpress_service = WordPressService()
        semrush_service = SEMrushService()
        google_service = GoogleService()
        report_service = ReportService()

        # Gather all data
        data = {
            'wordpress': wordpress_service.get_stats(),
            'semrush': semrush_service.get_stats(),
            'ga4': google_service.get_ga4_stats(),
            'gbp': google_service.get_gbp_stats()
        }

        # Generate report
        report = report_service.generate_report(data)

        # Save monthly report
        filename = f"monthly_report_{datetime.now().strftime('%Y_%m')}.json"
        report_service.export_to_json(report, filename)

        # Create backup
        report_service.create_backup(report, 'monthly')

        logger.info(f"Monthly report generated and saved: {filename}")

    except Exception as e:
        logger.error(f"Error in monthly report generation: {str(e)}")

def setup_scheduler():
    """Initialize and configure the scheduler"""
    scheduler = BackgroundScheduler()

    # Daily ranking check at 9 AM
    scheduler.add_job(
        check_keyword_rankings,
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_ranking_check',
        name='Daily Keyword Ranking Check'
    )

    # Weekly GBP posts every Monday at 10 AM
    scheduler.add_job(
        upload_weekly_gbp_photos,
        trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
        id='weekly_gbp_upload',
        name='Weekly GBP Photo Upload'
    )

    # Monthly report on the 1st at 8 AM
    scheduler.add_job(
        generate_monthly_report,
        trigger=CronTrigger(day=1, hour=8, minute=0),
        id='monthly_report',
        name='Monthly Report Generation'
    )

    logger.info("Scheduler configured with automated tasks")
    return scheduler

def start_scheduler():
    """Start the background scheduler"""
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Background scheduler started")
    return scheduler

def stop_scheduler(scheduler):
    """Stop the scheduler gracefully"""
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")