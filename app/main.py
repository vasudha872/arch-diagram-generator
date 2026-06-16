from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.fetcher import fetch_repo_files
import os

load_dotenv()

app = FastAPI(
    title="Architecture Diagram Generator",
    description="Generates visual architecture diagrams from GitHub repos using AI",
    version="0.1.0"
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class RepoRequest(BaseModel):
    github_url: str


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


@app.post("/fetch")
def fetch_repo(request: RepoRequest):
    """
    Takes a GitHub URL and returns all useful files in the repo.
    """
    try:
        result = fetch_repo_files(request.github_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))