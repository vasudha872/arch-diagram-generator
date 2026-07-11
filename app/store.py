from dataclasses import dataclass, field
from typing import Dict, List
from collections import defaultdict
import os


@dataclass
class FileStore:
    """
    In-memory store for all files fetched from a GitHub repo.
    Organizes files by type for easy access by the parser.
    """
    repo_name: str = ""
    files: Dict[str, str] = field(default_factory=dict)  # path -> content
    files_by_type: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    metadata: Dict = field(default_factory=dict)

    def add_file(self, path: str, content: str):
        """Add a file to the store."""
        self.files[path] = content

        # Organize by extension
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        self.files_by_type[ext].append(path)

    def get_files_by_extension(self, ext: str) -> Dict[str, str]:
        """Get all files of a specific type. Example: get_files_by_extension('.py')"""
        paths = self.files_by_type.get(ext, [])
        return {path: self.files[path] for path in paths}

    def get_summary(self) -> Dict:
        """Get a summary of what's in the store."""
        type_counts = {
            ext: len(paths)
            for ext, paths in self.files_by_type.items()
        }
        return {
            "repo": self.repo_name,
            "total_files": len(self.files),
            "files_by_type": type_counts,
            "all_paths": list(self.files.keys())
        }

    def is_empty(self) -> bool:
        return len(self.files) == 0