import logging
import os
from logging.handlers import RotatingFileHandler
import requests
from datetime import datetime

def setup_logger():
    logger = logging.getLogger('seo_automation')
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/seo_automation.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger():
    return logging.getLogger('seo_automation')

class SlackNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    def send_notification(self, message, level='info'):
        if not self.webhook_url:
            return

        try:
            emoji_map = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅'
            }

            payload = {
                'text': f"{emoji_map.get(level, 'ℹ️')} SEO Automation: {message}",
                'username': 'SEO Automation Bot',
                'icon_emoji': ':robot_face:'
            }

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

        except Exception as e:
            print(f"Failed to send Slack notification: {str(e)}")

# Global slack notifier
slack_notifier = SlackNotifier()

def log_and_notify(message, level='info', notify_slack=False):
    logger = get_logger()

    if level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)

    if notify_slack and level in ['error', 'warning']:
        slack_notifier.send_notification(message, level)