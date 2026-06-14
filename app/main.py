from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Architecture Diagram Generator",
    description="Generates visual architecture diagrams from GitHub repos using AI",
    version="0.1.0"
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "github_token_loaded": GITHUB_TOKEN is not None,
        "version": "0.1.0"
    }


@app.get("/")
def root():
    return {
        "message": "Architecture Diagram Generator API",
        "docs": "/docs",
        "health": "/health"
    }