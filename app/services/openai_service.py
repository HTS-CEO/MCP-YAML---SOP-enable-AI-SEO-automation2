import openai
import os
from app.utils.logger import get_logger
import time

class OpenAIService:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.logger = get_logger()

    def generate_blog_post(self, keyword, secondary_keywords=''):
        try:
            prompt = f"""
            Write a comprehensive, SEO-optimized blog post about "{keyword}".
            Additional keywords to include: {secondary_keywords}

            Requirements:
            - Length: 900-1200 words
            - Include SEO title and meta description
            - Use H1, H2, H3 headings
            - Include FAQ section at the end
            - Natural, engaging content
            - Include relevant statistics and data
            - End with a call-to-action

            Format the response as JSON with keys: title, content, seo_title, seo_description, faq
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            result = json.loads(content)

            self.logger.info(f"Blog post generated for keyword: {keyword}")
            return result

        except Exception as e:
            self.logger.error(f"OpenAI blog generation error: {str(e)}")
            # Fallback content
            return {
                'title': f"Complete Guide to {keyword}",
                'content': f"<h1>Complete Guide to {keyword}</h1><p>This is a comprehensive guide about {keyword}...</p>",
                'seo_title': f"{keyword} - Complete Guide 2025",
                'seo_description': f"Learn everything about {keyword} with this comprehensive guide.",
                'faq': "<h2>Frequently Asked Questions</h2><p>Q: What is {keyword}?<br>A: {keyword} is...</p>"
            }

    def reoptimize_content(self, existing_content, keywords):
        try:
            prompt = f"""
            Re-optimize the following blog post content for better SEO performance.
            Target keywords: {keywords}

            Original content:
            {existing_content}

            Requirements:
            - Improve keyword density and placement
            - Enhance readability and engagement
            - Update statistics if needed
            - Maintain original length approximately
            - Improve meta title and description

            Return as JSON with keys: title, content, seo_title, seo_description
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.6
            )

            content = response.choices[0].message.content.strip()
            import json
            result = json.loads(content)

            self.logger.info(f"Content re-optimized for keywords: {keywords}")
            return result

        except Exception as e:
            self.logger.error(f"OpenAI re-optimization error: {str(e)}")
            return {
                'title': "Re-optimized Content",
                'content': existing_content,
                'seo_title': f"Optimized Content - {keywords}",
                'seo_description': f"Re-optimized content for better SEO performance with keywords: {keywords}"
            }

    def generate_gbp_content(self, topic, max_length=150):
        try:
            prompt = f"""
            Create engaging content for Google Business Profile post about: {topic}

            Requirements:
            - Length: maximum {max_length} characters
            - Include call-to-action
            - Engaging and professional tone
            - Include relevant emoji or symbols

            Return as plain text.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )

            content = response.choices[0].message.content.strip()

            self.logger.info(f"GBP content generated for topic: {topic}")
            return content

        except Exception as e:
            self.logger.error(f"OpenAI GBP content error: {str(e)}")
            return f"Check out our latest insights on {topic}! Visit us today. #Business #Local"