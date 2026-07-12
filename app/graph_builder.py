from app.store import FileStore
from app.parser import build_dependency_graph
from app.config_parser import extract_config_data
from typing import Dict, List


# packages that are so common they clutter the diagram
NOISE_PACKAGES = {
    'os', 'sys', 'json', 're', 'math', 'time', 'datetime',
    'collections', 'itertools', 'functools', 'typing',
    'pathlib', 'abc', 'io', 'copy', 'enum', 'dataclasses',
    'logging', 'warnings', 'traceback', 'inspect',
    'react-dom', 'tslib', 'core-js'
}

# packages worth showing as nodes — they represent real architecture decisions
IMPORTANT_PACKAGES = {
    # Python web frameworks
    'fastapi', 'django', 'flask', 'tornado', 'starlette',
    # databases
    'sqlalchemy', 'sqlmodel', 'pymongo', 'redis', 'elasticsearch',
    'psycopg', 'psycopg2', 'motor', 'alembic',
    # auth and security
    'pyjwt', 'passlib', 'cryptography', 'authlib',
    # http clients
    'requests', 'httpx', 'aiohttp',
    # data and ML
    'pandas', 'numpy', 'scikit-learn', 'tensorflow',
    'torch', 'transformers', 'langchain', 'openai',
    # task queues
    'celery', 'dramatiq', 'rq',
    # cloud
    'boto3', 'google-cloud', 'azure',
    # JS frameworks
    'react', 'vue', 'angular', 'express', 'nextjs', 'next',
    'axios', 'tanstack', 'prisma', 'mongoose',
}

# folders that clutter the diagram without adding architectural value
NOISE_FOLDERS = {
    '.github', '.vscode', '.agents', '.claude',
    '.copier', '.pre-commit-config', 'node_modules',
    '__pycache__', '.git', 'dist', 'build'
}

# file types that aren't useful in an architecture diagram
NOISE_FILE_TYPES = {'other'}


def is_meaningful_node(node: dict, all_edges: list) -> bool:
    """
    Decide if a node is worth showing in the diagram.
    
    Rules:
    - Skip files in noise folders (.github, .vscode etc)
    - Skip __init__.py files (they're just package markers)
    - Skip nodes with no edges (isolated files)
    - Always keep package and service nodes
    - Always keep entry points
    """
    node_id = node["id"]
    node_type = node.get("type", "")
    label = node.get("label", "")

    # always keep package and service nodes
    if node_type in ("package", "service"):
        return True

    # skip noise file types
    if node_type in NOISE_FILE_TYPES:
        return False

    # skip files in noise folders
    for folder in NOISE_FOLDERS:
        if node_id.startswith(folder + '/') or ('/' + folder + '/') in node_id:
            return False

    # skip __init__.py — they're just package markers, not real architecture
    if label == '__init__.py':
        return False

    # skip isolated nodes (no edges at all)
    node_edge_ids = {e["from"] for e in all_edges} | {e["to"] for e in all_edges}
    if node_id not in node_edge_ids:
        return False

    return True


def assign_layer(node: dict) -> str:
    """
    Assign each node to an architectural layer.
    This is used for grouping in the diagram.
    """
    node_id = node["id"]
    node_type = node.get("type", "")

    if node_type == "package":
        return "packages"

    if node_type == "service":
        return "infrastructure"

    path_lower = node_id.lower()

    if 'frontend' in path_lower or 'client' in path_lower:
        return "frontend"

    if 'test' in path_lower or 'spec' in path_lower:
        return "tests"

    if 'backend' in path_lower or 'server' in path_lower:
        return "backend"

    if 'api' in path_lower or 'routes' in path_lower:
        return "api"

    if 'core' in path_lower or 'config' in path_lower:
        return "core"

    if 'db' in path_lower or 'model' in path_lower or 'migration' in path_lower:
        return "database"

    return "app"


def is_important_package(package: str) -> bool:
    """Check if a package is worth showing in the diagram."""
    package_lower = package.lower()

    if package_lower in NOISE_PACKAGES:
        return False

    if package_lower in IMPORTANT_PACKAGES:
        return True

    # always show database-related packages
    db_keywords = ['sql', 'db', 'mongo', 'redis', 'postgres',
                   'mysql', 'sqlite', 'database', 'orm']
    if any(kw in package_lower for kw in db_keywords):
        return True

    return False


def build_unified_graph(store: FileStore) -> Dict:
    """
    Main function: combine file dependency graph + config data
    into one unified graph spec ready for diagram rendering.

    Returns:
    {
        "nodes": [...],
        "edges": [...],
        "summary": {...}
    }
    """
    print("\nBuilding unified graph...")

    # Step 1: get file dependency graph
    file_graph = build_dependency_graph(store)

    # Step 2: get config data
    config_data = extract_config_data(store)

    # Step 3: start with all file nodes and edges
    nodes = list(file_graph["nodes"])
    edges = list(file_graph["edges"])
    node_ids = {n["id"] for n in nodes}

    # Step 4: add important package nodes
    all_packages = (
        config_data.get("python_packages", []) +
        config_data.get("js_packages", [])
    )

    important_packages = [
        p for p in all_packages
        if is_important_package(p)
    ]

    for package in important_packages:
        node_id = f"pkg:{package}"
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": package,
                "type": "package"
            })
            node_ids.add(node_id)

    # Step 5: add docker service nodes
    for service in config_data.get("docker_services", []):
        node_id = f"svc:{service['name']}"
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": service["name"],
                "type": "service",
                "image": service.get("image", ""),
                "ports": service.get("ports", [])
            })
            node_ids.add(node_id)

    # Step 6: connect entry point files to important packages
    entry_points = [
        n["id"] for n in nodes
        if n.get("type") == "python" and
        n["label"] in ('main.py', 'app.py', 'server.py')
    ]

    for entry in entry_points:
        for package in important_packages:
            node_id = f"pkg:{package}"
            edges.append({
                "from": entry,
                "to": node_id,
                "type": "depends_on"
            })

    # Step 7: connect docker services to each other
    for service in config_data.get("docker_services", []):
        from_id = f"svc:{service['name']}"
        for dep in service.get("depends_on", []):
            to_id = f"svc:{dep}"
            if to_id in node_ids:
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "type": "depends_on"
                })

    # Step 8: deduplicate edges
    unique_edges = []
    seen = set()
    for edge in edges:
        key = f"{edge['from']}->{edge['to']}"
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    # Step 8.5: filter out noise nodes and assign layers
    filtered_nodes = []
    for node in nodes:
        if is_meaningful_node(node, unique_edges):
            node["layer"] = assign_layer(node)
            filtered_nodes.append(node)

    # remove edges that reference filtered-out nodes
    filtered_node_ids = {n["id"] for n in filtered_nodes}
    filtered_edges = [
        e for e in unique_edges
        if e["from"] in filtered_node_ids
        and e["to"] in filtered_node_ids
    ]

    
    # Step 9: build summary
    node_types = {}
    layers = {}
    for node in filtered_nodes:
        t = node.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1
        l = node.get("layer", "app")
        layers[l] = layers.get(l, 0) + 1

    summary = {
        "total_nodes": len(filtered_nodes),
        "total_edges": len(filtered_edges),
        "node_types": node_types,
        "layers": layers,
        "important_packages": important_packages,
        "docker_services": [
            s["name"] for s in config_data.get("docker_services", [])
        ]
    }

    print(f"Unified graph: {len(filtered_nodes)} nodes, {len(filtered_edges)} edges")

    return {
        "nodes": filtered_nodes,
        "edges": filtered_edges,
        "summary": summary
    }