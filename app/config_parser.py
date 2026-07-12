import yaml
import json
from typing import Dict, List


def parse_requirements_txt(content: str) -> List[str]:
    """
    Extract package names from requirements.txt.
    
    Handles formats like:
        fastapi==0.100.0
        uvicorn>=0.20.0
        requests
        # this is a comment
    
    Returns: ['fastapi', 'uvicorn', 'requests']
    """
    packages = []
    for line in content.split('\n'):
        line = line.strip()
        # skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        # skip -r includes and -e editable installs
        if line.startswith('-'):
            continue
        # remove version specifiers: ==, >=, <=, ~=, !=
        for sep in ['==', '>=', '<=', '~=', '!=', '>',  '<', '[']:
            if sep in line:
                line = line.split(sep)[0]
        package = line.strip()
        if package:
            packages.append(package.lower())
    return packages


def parse_package_json(content: str) -> Dict:
    """
    Extract dependencies from package.json.
    
    Returns:
    {
        "dependencies": ["react", "express"],
        "devDependencies": ["jest", "typescript"],
        "scripts": ["start", "test", "build"]
    }
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"dependencies": [], "devDependencies": [], "scripts": []}

    deps = list(data.get("dependencies", {}).keys())
    dev_deps = list(data.get("devDependencies", {}).keys())
    scripts = list(data.get("scripts", {}).keys())

    return {
        "dependencies": deps,
        "devDependencies": dev_deps,
        "scripts": scripts
    }


def parse_docker_compose(content: str) -> Dict:
    """
    Extract service definitions from docker-compose.yaml.
    
    Returns:
    {
        "services": [
            {
                "name": "api",
                "image": "python:3.12",
                "ports": ["8000:8000"],
                "depends_on": ["db", "redis"]
            }
        ]
    }
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return {"services": []}

    if not data or "services" not in data:
        return {"services": []}

    services = []
    for service_name, config in data["services"].items():
        if not isinstance(config, dict):
            continue

        service = {
            "name": service_name,
            "image": config.get("image", "custom build"),
            "ports": config.get("ports", []),
            "depends_on": config.get("depends_on", [])
        }
        services.append(service)

    return {"services": services}


def parse_pyproject_toml(content: str) -> Dict:
    """
    Extract dependencies from pyproject.toml.
    Handles both poetry and PEP 517 formats.
    """
    deps = []
    in_deps_section = False

    # words that look like deps but are actually toml field names
    SKIP_WORDS = {
        'python', 'name', 'version', 'description', 'authors',
        'readme', 'requires-python', 'dependencies', 'license',
        'homepage', 'repository', 'documentation', 'keywords'
    }

    for line in content.split('\n'):
        line = line.strip()

        # detect dependency sections
        if line in ('[tool.poetry.dependencies]', '[project]', '[tool.poetry.dev-dependencies]'):
            in_deps_section = True
            continue

        # stop at next section
        if line.startswith('[') and in_deps_section:
            in_deps_section = False
            continue

        if in_deps_section and '=' in line and not line.startswith('#'):
            package = line.split('=')[0].strip().strip('"').lower()

            # remove version specifiers: >=, <=, >, <, ~=
            for spec in ['>=', '<=', '~=', '!=', '>', '<']:
                if spec in package:
                    package = package.split(spec)[0]

            # remove extras like [standard], [binary], [argon2,bcrypt]
            if '[' in package:
                package = package.split('[')[0]

            package = package.strip()

            # skip field names and single-char entries
            if package in SKIP_WORDS or len(package) < 2:
                continue

            # skip if it looks like a toml key not a package
            if '-python' in package or package.startswith('tool'):
                continue

            deps.append(package)

    return {"dependencies": deps}

def extract_config_data(store) -> Dict:
    """
    Main function: scan all files in the store for config files
    and extract dependency/service information.
    
    Returns a unified config report.
    """
    result = {
        "python_packages": [],
        "js_packages": [],
        "js_dev_packages": [],
        "docker_services": [],
        "scripts": []
    }

    for file_path, content in store.files.items():
        filename = file_path.split('/')[-1].lower()

        if filename == 'requirements.txt':
            packages = parse_requirements_txt(content)
            result["python_packages"].extend(packages)
            print(f"Parsed requirements.txt: {len(packages)} packages")

        elif filename == 'package.json':
            pkg_data = parse_package_json(content)
            result["js_packages"].extend(pkg_data["dependencies"])
            result["js_dev_packages"].extend(pkg_data["devDependencies"])
            result["scripts"].extend(pkg_data["scripts"])
            print(f"Parsed package.json: {len(pkg_data['dependencies'])} deps")

        elif filename in ('docker-compose.yml', 'docker-compose.yaml'):
            compose_data = parse_docker_compose(content)
            result["docker_services"].extend(compose_data["services"])
            print(f"Parsed docker-compose: {len(compose_data['services'])} services")

        elif filename == 'pyproject.toml':
            toml_data = parse_pyproject_toml(content)
            result["python_packages"].extend(toml_data["dependencies"])
            print(f"Parsed pyproject.toml: {len(toml_data['dependencies'])} deps")

    # deduplicate
    result["python_packages"] = sorted(set(result["python_packages"]))
    result["js_packages"] = sorted(set(result["js_packages"]))
    result["js_dev_packages"] = sorted(set(result["js_dev_packages"]))

    return result