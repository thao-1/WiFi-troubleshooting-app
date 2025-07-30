from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat
from app.core.config import settings
from dotenv import load_dotenv
import os
import pathlib

# Load environment variables from .env file
env_path = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


app = FastAPI(
    title="WiFi Troubleshooting Chatbot",
    description="A chatbot to help users troubleshoot WiFi issues.",
    version="1.0.0",
)

# Configuration CORS for React frontend
app.add_middleware(
    CORSMiddleware,     
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include chat routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "WiFi Troubleshooting Chatbot API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "OK"}
