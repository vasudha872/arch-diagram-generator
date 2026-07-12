from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.fetcher import fetch_repo_files
from app.analyzer import analyze_repo
from app.parser import build_dependency_graph
from app.analyzer import build_file_store
from app.config_parser import extract_config_data
from app.graph_builder import build_unified_graph
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
    

@app.post("/analyze")
def analyze(request: RepoRequest):
    """
    Main endpoint: analyze a GitHub repo and return
    a structured report about its architecture.
    """
    try:
        result = analyze_repo(request.github_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/graph")
def get_dependency_graph(request: RepoRequest):
    """
    Build and return a dependency graph for a GitHub repo.
    Shows which files import which.
    """
    try:
        store = build_file_store(request.github_url)
        graph = build_dependency_graph(store)
        return graph
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/config")
def get_config_data(request: RepoRequest):
    """
    Parse config files in a repo — requirements.txt,
    package.json, docker-compose.yaml — and return
    a unified dependency report.
    """
    try:
        store = build_file_store(request.github_url)
        config = extract_config_data(store)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/unified-graph")
def get_unified_graph(request: RepoRequest):
    """
    The main output endpoint. Returns a complete graph spec
    combining file dependencies + package dependencies +
    docker services. Ready for diagram rendering.
    """
    try:
        store = build_file_store(request.github_url)
        graph = build_unified_graph(store)
        return graph
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))