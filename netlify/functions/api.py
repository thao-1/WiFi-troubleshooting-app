import os
import sys
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.main import app as fastapi_app

# Configure CORS for Netlify
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(fastapi_app)

def lambda_handler(event, context):
    """Netlify Functions handler"""
    return handler(event, context)
