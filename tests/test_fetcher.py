from app.fetcher import parse_github_url, is_useful_file
from app.parser import extract_python_imports, extract_js_imports, is_internal_import
from app.config_parser import parse_requirements_txt, parse_package_json, parse_docker_compose

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

def test_extract_python_imports():
    code = """
import os
from app.fetcher import fetch_repo_files
from dotenv import load_dotenv
"""
    imports = extract_python_imports(code, "test.py")
    assert 'os' in imports
    assert 'app.fetcher' in imports
    assert 'dotenv' in imports

def test_extract_js_imports():
    code = """
import express from 'express'
import { useState } from 'react'
const router = require('./router')
"""
    imports = extract_js_imports(code, "test.js")
    assert 'express' in imports
    assert 'react' in imports
    assert './router' in imports

def test_is_internal_import_relative():
    assert is_internal_import('./router', ['src/router.js']) == True

def test_is_internal_import_external():
    assert is_internal_import('fastapi', ['app/main.py']) == False

def test_is_internal_import_internal():
    assert is_internal_import('app.fetcher', ['app/fetcher.py']) == True


def test_parse_requirements_txt():
    content = """
fastapi==0.100.0
uvicorn>=0.20.0
# this is a comment
requests
-r other.txt
"""
    packages = parse_requirements_txt(content)
    assert 'fastapi' in packages
    assert 'uvicorn' in packages
    assert 'requests' in packages
    assert 'this is a comment' not in packages

def test_parse_package_json():
    content = '{"dependencies": {"react": "^18.0.0", "axios": "^1.0.0"}, "devDependencies": {"typescript": "^5.0.0"}, "scripts": {"start": "node index.js"}}'
    result = parse_package_json(content)
    assert 'react' in result['dependencies']
    assert 'axios' in result['dependencies']
    assert 'typescript' in result['devDependencies']
    assert 'start' in result['scripts']

def test_parse_docker_compose():
    content = """
services:
  api:
    image: python:3.12
    ports:
      - "8000:8000"
  db:
    image: postgres:15
    depends_on: []
"""
    result = parse_docker_compose(content)
    names = [s['name'] for s in result['services']]
    assert 'api' in names
    assert 'db' in names


from app.graph_builder import is_meaningful_node, assign_layer

def test_is_meaningful_node_keeps_package():
    node = {"id": "pkg:fastapi", "type": "package", "label": "fastapi"}
    edges = []
    assert is_meaningful_node(node, edges) == True

def test_is_meaningful_node_removes_github_folder():
    node = {"id": ".github/workflows/ci.yml", "type": "other", "label": "ci.yml"}
    edges = []
    assert is_meaningful_node(node, edges) == False

def test_is_meaningful_node_removes_init_files():
    node = {"id": "app/__init__.py", "type": "python", "label": "__init__.py"}
    edges = [{"from": "app/__init__.py", "to": "app/main.py", "type": "import"}]
    assert is_meaningful_node(node, edges) == False

def test_is_meaningful_node_removes_isolated_nodes():
    node = {"id": "app/utils.py", "type": "python", "label": "utils.py"}
    edges = []
    assert is_meaningful_node(node, edges) == False

def test_assign_layer_backend():
    node = {"id": "backend/app/main.py", "type": "python"}
    assert assign_layer(node) == "backend"

def test_assign_layer_frontend():
    node = {"id": "frontend/src/App.tsx", "type": "javascript"}
    assert assign_layer(node) == "frontend"

def test_assign_layer_package():
    node = {"id": "pkg:fastapi", "type": "package"}
    assert assign_layer(node) == "packages"

def test_assign_layer_service():
    node = {"id": "svc:postgres", "type": "service"}
    assert assign_layer(node) == "infrastructure"

def test_assign_layer_tests():
    node = {"id": "tests/test_main.py", "type": "python"}
    assert assign_layer(node) == "tests"