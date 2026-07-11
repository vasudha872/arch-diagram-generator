import os
from github import Github
from dotenv import load_dotenv
from app.store import FileStore

load_dotenv()

# File types we care about
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx',
    '.yaml', '.yml', '.json', '.toml', '.env.example'
}

# Files to skip
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

    for part in parts:
        if part in IGNORED_DIRS:
            return False

    filename = parts[-1]

    if filename in IGNORED_FILES:
        return False

    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    url = url.rstrip('/')
    parts = url.replace('https://github.com/', '').split('/')

    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")

    return parts[0], parts[1]


def fetch_repo_files(github_url: str) -> dict:
    """
    Main function: given a GitHub URL, fetch all useful files
    and return them organized in a FileStore.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env file")

    g = Github(token)
    owner, repo_name = parse_github_url(github_url)
    print(f"\nFetching repo: {owner}/{repo_name}")

    repo = g.get_repo(f"{owner}/{repo_name}")

    # Create a fresh store for this repo
    store = FileStore(repo_name=f"{owner}/{repo_name}")

    # Get all contents recursively
    contents = repo.get_git_tree(sha="HEAD", recursive=True)

    skipped = 0
    errors = 0

    for item in contents.tree:
        if item.type != "blob":
            continue

        file_path = item.path

        if not is_useful_file(file_path):
            skipped += 1
            continue

        if item.size > 100000:
            print(f"Skipping large file: {file_path} ({item.size} bytes)")
            skipped += 1
            continue

        try:
            file_content = repo.get_contents(file_path)
            content = file_content.decoded_content.decode('utf-8')
            store.add_file(file_path, content)
            print(f"Fetched: {file_path}")
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            errors += 1
            continue

    # Add metadata to store
    store.metadata = {
        "skipped_files": skipped,
        "error_count": errors,
        "github_url": github_url
    }

    print(f"\nDone. {len(store.files)} files fetched, {skipped} skipped, {errors} errors.")
    return store.get_summary()