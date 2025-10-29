import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

def handler(event, context):
    from serverless_wsgi import handle_request
    return handle_request(app, event, context)