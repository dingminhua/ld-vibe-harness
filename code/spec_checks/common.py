"""Shared helpers for LDVH specs checks."""

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Issue:
    path: Path
    line: int
    message: str
    code: str = None

    def format(self, root=None):
        display_path = self.path
        if root:
            try:
                display_path = self.path.relative_to(root)
            except ValueError:
                display_path = self.path
        if self.code:
            return f"{display_path}:{self.line}: [{self.code}] {self.message}"
        return f"{display_path}:{self.line}: {self.message}"


def relative_path(path, root=None):
    root = root or PROJECT_ROOT
    try:
        return str(Path(path).resolve().relative_to(root))
    except ValueError:
        return str(path)


def count_by(items, key):
    counts = {}
    for item in items:
        value = item.get(key) or "(empty)"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def is_project_local(path, root=None):
    root = root or PROJECT_ROOT
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False
