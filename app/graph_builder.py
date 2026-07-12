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

    # Step 9: build summary
    node_types = {}
    for node in nodes:
        t = node.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1

    summary = {
        "total_nodes": len(nodes),
        "total_edges": len(unique_edges),
        "node_types": node_types,
        "important_packages": important_packages,
        "docker_services": [
            s["name"] for s in config_data.get("docker_services", [])
        ]
    }

    print(f"Unified graph: {len(nodes)} nodes, {len(unique_edges)} edges")

    return {
        "nodes": nodes,
        "edges": unique_edges,
        "summary": summary
    }