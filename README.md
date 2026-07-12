# Architecture Diagram Generator

> Point it at any GitHub repo. Get back a structured map of how the project is organized.

## What it does

Most developers waste hours trying to understand a new codebase. This tool reads any GitHub repository, analyzes the files, and returns a structured report showing:

- What type of project it is (FastAPI, Django, React, Node.js, etc.)
- Where execution starts (entry points)
- How files are organized by type
- Top level modules and services
- Configuration files that reveal infrastructure

## Demo

**Input:**
```json
POST /analyze
{
  "github_url": "https://github.com/expressjs/express"
}
```

**Output:**
```json
{
  "repo": "expressjs/express",
  "project_type": "JavaScript/Node.js project",
  "total_files": 80,
  "entry_points": ["index.js"],
  "config_files": ["package.json"],
  "top_level_modules": ["lib", "examples", "test"]
}
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python) |
| GitHub Integration | PyGitHub |
| File Analysis | Custom AST-based analyzer |
| Testing | pytest |
| Server | uvicorn |

## Project Status

- [x] Week 1 — GitHub fetcher + file analyzer
- [ ] Week 2 — AST parser + dependency graph
- [ ] Week 3 — AI analysis layer (Claude API + RAG)
- [ ] Week 4 — Interactive diagram UI (Mermaid.js)
- [ ] Week 5 — Deploy + launch

## How to Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/vasudha872/arch-diagram-generator
cd arch-diagram-generator
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your GitHub token**
```bash
# Create a .env file and add:
GITHUB_TOKEN=your_github_token_here
```

**5. Run the server**
```bash
uvicorn app.main:app --reload
```

**6. Open the API explorer**
http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check server status |
| GET | `/` | API info |
| POST | `/fetch` | Fetch and organize repo files |
| POST | `/analyze` | Full repo analysis report |

## Architecture

GitHub URL
↓
fetcher.py — connects to GitHub API, downloads files
↓
store.py — organizes files by type in memory
↓
analyzer.py — detects project type, finds entry points
↓
main.py — FastAPI endpoints expose everything via HTTP
