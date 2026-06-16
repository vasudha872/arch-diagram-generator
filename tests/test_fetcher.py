from app.fetcher import parse_github_url, is_useful_file

def test_parse_github_url():
    owner, repo = parse_github_url("https://github.com/microsoft/vscode")
    assert owner == "microsoft"
    assert repo == "vscode"

def test_parse_github_url_trailing_slash():
    owner, repo = parse_github_url("https://github.com/microsoft/vscode/")
    assert owner == "microsoft"
    assert repo == "vscode"

def test_is_useful_file_python():
    assert is_useful_file("app/main.py") == True

def test_is_useful_file_javascript():
    assert is_useful_file("src/index.js") == True

def test_is_useful_file_ignored_dir():
    assert is_useful_file("node_modules/lodash/index.js") == False

def test_is_useful_file_lockfile():
    assert is_useful_file("package-lock.json") == False

def test_is_useful_file_image():
    assert is_useful_file("assets/logo.png") == False