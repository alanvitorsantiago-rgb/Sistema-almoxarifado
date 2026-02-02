from app import app

# Vercel serverless handler
def handler(request, response):
    return app(request, response)
