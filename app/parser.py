import ast
from typing import Dict, List
from app.store import FileStore


def extract_python_imports(file_content: str, file_path: str) -> List[str]:
    """
    Extract all imports from a Python file using Python's built-in AST.
    
    For a file containing:
        import os
        from app.fetcher import fetch_repo_files
    
    Returns: ['os', 'app.fetcher']
    """
    imports = []

    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        print(f"Could not parse {file_path} — skipping")
        return imports

    for node in ast.walk(tree):
        # handles: import os, import sys
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        # handles: from app.fetcher import fetch_repo_files
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def extract_js_imports(file_content: str, file_path: str) -> List[str]:
    """
    Extract imports from a JavaScript/TypeScript file using simple line parsing.
    
    Handles:
        import express from 'express'
        const router = require('./router')
        import { useState } from 'react'
    
    Returns: ['express', './router', 'react']
    """
    imports = []
    lines = file_content.split('\n')

    for line in lines:
        line = line.strip()

        # handles: import x from 'y'  or  import { x } from 'y'
        if line.startswith('import ') and ' from ' in line:
            try:
                # get the part after 'from'
                from_part = line.split(' from ')[-1]
                # remove quotes, semicolons, whitespace
                module = from_part.strip().strip("'\"").rstrip(';').strip()
                if module:
                    imports.append(module)
            except Exception:
                continue

        # handles: const x = require('y')
        elif 'require(' in line:
            try:
                start = line.index('require(') + 8
                end = line.index(')', start)
                module = line[start:end].strip().strip("'\"")
                if module:
                    imports.append(module)
            except Exception:
                continue

    return imports


def is_internal_import(module: str, all_file_paths: List[str]) -> bool:
    """
    Check if an import refers to a file inside the repo (internal)
    or an external library (external).
    
    Examples:
        'os' → external (standard library)
        'fastapi' → external (third party)
        'app.fetcher' → internal (our own code)
        './router' → internal (relative import)
    """
    # relative imports are always internal
    if module.startswith('.'):
        return True

    # convert module path to file path format
    # 'app.fetcher' → 'app/fetcher'
    module_as_path = module.replace('.', '/')

    # check if any file in the repo matches this module path
    for file_path in all_file_paths:
        # remove extension for comparison
        path_without_ext = file_path.rsplit('.', 1)[0]
        if path_without_ext == module_as_path:
            return True
        if path_without_ext.endswith('/' + module_as_path):
            return True

    return False


def build_dependency_graph(store: FileStore) -> dict:
    """
    Main function: reads every file in the store and builds
    a dependency graph showing which files import which.
    
    Returns:
    {
        "nodes": [
            {"id": "app/main.py", "label": "main.py", "type": "python"}
        ],
        "edges": [
            {"from": "app/main.py", "to": "app/fetcher.py", "type": "import"}
        ],
        "summary": {
            "total_nodes": 6,
            "total_edges": 4,
            "internal_deps": 4,
            "external_deps": 12
        }
    }
    """
    nodes = []
    edges = []
    all_paths = list(store.files.keys())
    external_deps = set()

    print(f"\nBuilding dependency graph for {len(all_paths)} files...")

    for file_path, content in store.files.items():
        # determine file type
        if file_path.endswith('.py'):
            file_type = 'python'
            imports = extract_python_imports(content, file_path)
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            file_type = 'javascript'
            imports = extract_js_imports(content, file_path)
        else:
            file_type = 'other'
            imports = []

        # add this file as a node
        label = file_path.split('/')[-1]
        nodes.append({
            "id": file_path,
            "label": label,
            "type": file_type
        })

        # process each import
        for module in imports:
            if is_internal_import(module, all_paths):
                # find the actual file path this import refers to
                module_as_path = module.replace('.', '/')
                target = None

                for path in all_paths:
                    path_without_ext = path.rsplit('.', 1)[0]
                    if path_without_ext == module_as_path:
                        target = path
                        break
                    if path_without_ext.endswith('/' + module_as_path):
                        target = path
                        break

                if target and target != file_path:
                    edges.append({
                        "from": file_path,
                        "to": target,
                        "type": "import"
                    })
            else:
                # track external dependencies
                top_level = module.split('.')[0]
                external_deps.add(top_level)

    # remove duplicate edges
    unique_edges = []
    seen = set()
    for edge in edges:
        key = f"{edge['from']}->{edge['to']}"
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    print(f"Graph built: {len(nodes)} nodes, {len(unique_edges)} edges")
    print(f"External dependencies found: {sorted(external_deps)}")

    return {
        "nodes": nodes,
        "edges": unique_edges,
        "external_dependencies": sorted(external_deps),
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(unique_edges),
            "external_deps": len(external_deps)
        }
    }
