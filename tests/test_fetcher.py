from app.fetcher import parse_github_url, is_useful_file
from app.parser import extract_python_imports, extract_js_imports, is_internal_import

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