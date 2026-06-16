import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

# File types we care about
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx',
    '.yaml', '.yml', '.json', '.toml', '.env.example'
}

# Files to skip — too big or not useful
IGNORED_FILES = {
    'package-lock.json', 'yarn.lock',
    'poetry.lock', 'Pipfile.lock'
}

# Folders to skip
IGNORED_DIRS = {
    'node_modules', 'venv', '.git',
    '__pycache__', 'dist', 'build', '.next'
}


def get_file_extension(filename: str) -> str:
    """Get the extension of a file."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def is_useful_file(file_path: str) -> bool:
    """Check if a file is worth analyzing."""
    parts = file_path.split('/')

    # Skip if inside an ignored folder
    for part in parts:
        if part in IGNORED_DIRS:
            return False

    filename = parts[-1]

    # Skip ignored files
    if filename in IGNORED_FILES:
        return False

    # Only include allowed extensions
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL.
    
    Example:
        https://github.com/microsoft/vscode
        returns ('microsoft', 'vscode')
    """
    # Remove trailing slash if present
    url = url.rstrip('/')

    # Remove https://github.com/
    parts = url.replace('https://github.com/', '').split('/')

    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner = parts[0]
    repo = parts[1]
    return owner, repo


def fetch_repo_files(github_url: str) -> dict:
    """
    Main function: given a GitHub URL, return all useful files.
    
    Returns a dict like:
    {
        "repo": "owner/reponame",
        "files": {
            "path/to/file.py": "file content here...",
            "another/file.js": "more content..."
        },
        "file_count": 12
    }
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env file")

    # Connect to GitHub
    g = Github(token)

    # Parse the URL to get owner and repo name
    owner, repo_name = parse_github_url(github_url)
    print(f"Fetching repo: {owner}/{repo_name}")

    # Get the repo object
    repo = g.get_repo(f"{owner}/{repo_name}")

    # Get all contents recursively
    files = {}
    contents = repo.get_git_tree(sha="HEAD", recursive=True)

    for item in contents.tree:
        # Only process files (not folders)
        if item.type != "blob":
            continue

        file_path = item.path

        # Skip files we don't care about
        if not is_useful_file(file_path):
            continue

        # Skip files larger than 100KB (too big for analysis)
        if item.size > 100000:
            print(f"Skipping large file: {file_path} ({item.size} bytes)")
            continue

        # Fetch the actual file content
        try:
            file_content = repo.get_contents(file_path)
            content = file_content.decoded_content.decode('utf-8')
            files[file_path] = content
            print(f"Fetched: {file_path}")
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            continue

    return {
        "repo": f"{owner}/{repo_name}",
        "files": files,
        "file_count": len(files)
    }