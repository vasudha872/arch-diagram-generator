import os
from app.store import FileStore
from app.fetcher import fetch_repo_files, parse_github_url
from github import Github
from dotenv import load_dotenv

load_dotenv()

# Files that are likely entry points of a project
ENTRY_POINT_NAMES = {
    'main.py', 'app.py', 'server.py', 'index.py',
    'index.js', 'index.ts', 'server.js', 'server.ts',
    'app.js', 'app.ts', 'manage.py', 'wsgi.py', 'asgi.py'
}

# Config files that reveal project structure
CONFIG_FILES = {
    'docker-compose.yml', 'docker-compose.yaml',
    'dockerfile', 'kubernetes.yml', 'k8s.yml',
    'package.json', 'pyproject.toml', 'setup.py',
    'requirements.txt', '.env.example'
}


def find_entry_points(store: FileStore) -> list:
    """
    Find the main entry point files in the repo.
    These are the files where execution starts.
    """
    entry_points = []

    for file_path in store.files.keys():
        filename = file_path.split('/')[-1].lower()
        if filename in ENTRY_POINT_NAMES:
            entry_points.append(file_path)

    return entry_points


def find_config_files(store: FileStore) -> list:
    """
    Find configuration files that reveal how the project is structured.
    """
    config_files = []

    for file_path in store.files.keys():
        filename = file_path.split('/')[-1].lower()
        if filename in CONFIG_FILES:
            config_files.append(file_path)

    return config_files


def find_top_level_modules(store: FileStore) -> list:
    """
    Find top level folders/modules in the repo.
    These usually represent major components or services.
    """
    modules = set()

    for file_path in store.files.keys():
        parts = file_path.split('/')
        if len(parts) > 1:
            modules.add(parts[0])

    return sorted(list(modules))


def detect_project_type(store: FileStore) -> str:
    """
    Guess what kind of project this is based on files present.
    """
    all_paths = ' '.join(store.files.keys()).lower()
    file_types = store.files_by_type

    if '.py' in file_types and len(file_types.get('.py', [])) > 5:
        if 'fastapi' in ' '.join(store.files.values()).lower():
            return "FastAPI (Python web API)"
        if 'django' in ' '.join(store.files.values()).lower():
            return "Django (Python web framework)"
        if 'flask' in ' '.join(store.files.values()).lower():
            return "Flask (Python web framework)"
        return "Python project"

    if '.ts' in file_types or '.tsx' in file_types:
        if 'react' in all_paths or '.tsx' in file_types:
            return "React/TypeScript frontend"
        return "TypeScript project"

    if '.js' in file_types:
        return "JavaScript/Node.js project"

    return "Mixed/Unknown project type"


def build_file_store(github_url: str) -> FileStore:
    """
    Fetch files from a GitHub repo, prioritizing important files first.
    """
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)

    owner, repo_name = parse_github_url(github_url)
    repo = g.get_repo(f"{owner}/{repo_name}")

    store = FileStore(repo_name=f"{owner}/{repo_name}")
    contents = repo.get_git_tree(sha="HEAD", recursive=True)

    from app.fetcher import is_useful_file

    # Separate files into priority buckets
    high_priority = []   # config files and entry points
    medium_priority = [] # source code files
    low_priority = []    # test files and examples

    for item in contents.tree:
        if item.type != "blob":
            continue
        if not is_useful_file(item.path):
            continue
        if item.size > 100000:
            continue

        filename = item.path.split('/')[-1].lower()
        path_lower = item.path.lower()

        # High priority: config and entry point files
        if filename in CONFIG_FILES or filename in ENTRY_POINT_NAMES:
            high_priority.append(item)
        # Low priority: test files and examples
        elif 'test' in path_lower or 'example' in path_lower or 'spec' in path_lower:
            low_priority.append(item)
        # Medium priority: everything else (actual source code)
        else:
            medium_priority.append(item)

    # Fetch in priority order: high → medium → low
    ordered = high_priority + medium_priority + low_priority

    MAX_FILES = 80
    fetched_count = 0

    for item in ordered:
        if fetched_count >= MAX_FILES:
            print(f"Reached file limit of {MAX_FILES}, stopping.")
            break

        try:
            file_content = repo.get_contents(item.path)
            content = file_content.decoded_content.decode('utf-8')
            store.add_file(item.path, content)
            fetched_count += 1
            print(f"Fetched: {item.path}")
        except Exception as e:
            print(f"Could not read {item.path}: {e}")
            continue

    return store


def analyze_repo(github_url: str) -> dict:
    """
    Main function: analyze a GitHub repo and return
    a structured report about its architecture.
    """
    print(f"\nAnalyzing: {github_url}")

    # Step 1: fetch all files into the store
    store = build_file_store(github_url)

    if store.is_empty():
        return {"error": "No analyzable files found in this repo"}

    # Step 2: analyze the store
    entry_points = find_entry_points(store)
    config_files = find_config_files(store)
    top_modules = find_top_level_modules(store)
    project_type = detect_project_type(store)

    # Step 3: build the report
    report = {
        "repo": store.repo_name,
        "project_type": project_type,
        "total_files": len(store.files),
        "files_by_type": {
            ext: len(paths)
            for ext, paths in store.files_by_type.items()
        },
        "entry_points": entry_points,
        "config_files": config_files,
        "top_level_modules": top_modules,
        "all_paths": list(store.files.keys())
    }

    print(f"Analysis complete: {project_type}, {len(store.files)} files")
    return report