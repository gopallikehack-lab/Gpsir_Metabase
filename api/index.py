import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import main

# Vercel serverless handler
def handler(request):
    # For Vercel, we use polling mode in a separate process
    # This file is just to keep Vercel happy
    return {"status": "ok", "message": "Bot is running"}
