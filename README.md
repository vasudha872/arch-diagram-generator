# Architecture Diagram Generator

> Point it at any GitHub repo. Get back a structured map of how the project is organized — files, dependencies, services, all connected.

## What it does

Most developers waste hours trying to understand a new codebase. This tool reads any GitHub repository and returns a complete architecture map showing:

- What type of project it is (FastAPI, Django, React, Node.js, etc.)
- How files connect to each other (import dependencies)
- What external packages the project depends on
- What infrastructure services exist (Docker containers, databases, caches)
- How services depend on each other

## Demo

**Input:**
```json
POST /unified-graph
{
  "github_url": "https://github.com/tiangolo/full-stack-fastapi-template"
}
```

**Output:**
```json
{
  "nodes": [
    {"id": "backend/app/main.py", "label": "main.py", "type": "python", "layer": "backend"},
    {"id": "pkg:fastapi", "label": "fastapi", "type": "package", "layer": "packages"},
    {"id": "svc:db", "label": "db", "type": "service", "layer": "infrastructure"}
  ],
  "edges": [
    {"from": "backend/app/main.py", "to": "backend/app/api/main.py", "type": "import"},
    {"from": "svc:backend", "to": "svc:db", "type": "depends_on"}
  ],
  "summary": {
    "total_nodes": 33,
    "total_edges": 56,
    "layers": {"backend": 17, "packages": 11, "infrastructure": 5}
  }
}
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python) |
| GitHub Integration | PyGitHub |
| Code Parsing | Python AST + custom JS parser |
| Config Parsing | PyYAML + JSON |
| Graph Building | Custom graph builder |
| Testing | pytest |
| Server | uvicorn |

## Project Status

- [x] Week 1 — GitHub fetcher + file analyzer + FileStore
- [x] Week 2 — AST parser + dependency graph + config parser + unified graph
- [ ] Week 3 — AI analysis layer (Claude API + RAG)
- [ ] Week 4 — Interactive diagram UI (Mermaid.js)
- [ ] Week 5 — Deploy + launch

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check server status |
| GET | `/` | API info |
| POST | `/fetch` | Fetch and organize repo files |
| POST | `/analyze` | Project type + entry points report |
| POST | `/graph` | File dependency graph |
| POST | `/config` | Package and service dependencies |
| POST | `/unified-graph` | Complete architecture map (main endpoint) |

## Pipeline Architecture

GitHub URL
↓
fetcher.py — connects to GitHub API, fetches files with smart prioritization
↓
store.py — organizes files by type in memory (FileStore)
↓
parser.py — AST analysis, extracts import relationships
config_parser.py — parses requirements.txt, package.json, docker-compose
↓
graph_builder.py — combines everything into unified graph spec
- filters noise nodes (.github, init.py, isolated files)
- assigns layers (backend, frontend, packages, infrastructure)
- connects docker services via depends_on edges
↓
main.py — FastAPI endpoints expose everything via HTTP


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

## What's Coming

Week 3 adds the AI layer — feeding the unified graph into Claude API with RAG to understand what each service does, then generating natural language descriptions for every node. Week 4 renders everything as an interactive clickable diagram using Mermaid.js.

