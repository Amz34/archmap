import ast
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from archmap.graph import Node, Edge, ArchitectureGraph

@dataclass
class ScanResult:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

class CodeScanner:
    def __init__(self, root_dir: str, ignore_dirs: Optional[Set[str]] = None):
        self.root_dir = Path(os.path.abspath(root_dir))
        self.ignore_dirs = ignore_dirs or {
            ".git", "node_modules", "__pycache__", ".venv", "venv", 
            "dist", "build", "target", "env", ".hermes", "assets"
        }
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.internal_modules: Set[str] = set()

    def _get_module_name(self, file_path: Path) -> str:
        rel = file_path.relative_to(self.root_dir)
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _determine_layer(self, file_path: Path, content: str) -> str:
        path_str = str(file_path.relative_to(self.root_dir)).lower()
        if "test" in path_str or "tests/" in path_str:
            return "Test"
        if "cli" in path_str or "main.py" in path_str or "cmd/" in path_str:
            return "CLI / UI"
        if "service" in path_str or "logic" in path_str or "engine" in path_str:
            return "Service / Logic"
        if "model" in path_str or "db" in path_str or "storage" in path_str or "schema" in path_str:
            return "Data / Model"
        if "util" in path_str or "common" in path_str or "helper" in path_str:
            return "Utils / Shared"
        return "Core / App"

    def scan_python_file(self, file_path: Path) -> Node:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        lines = content.splitlines()
        loc = len(lines)
        
        module_name = self._get_module_name(file_path)
        node = Node(
            id=module_name,
            label=module_name.split(".")[-1] or module_name,
            path=str(file_path.relative_to(self.root_dir)),
            kind="module",
            layer=self._determine_layer(file_path, content),
            loc=loc,
            exports=[],
            metadata={"language": "python"}
        )

        try:
            tree = ast.parse(content)
            for item in tree.body:
                if isinstance(item, (ast.Import, ast.ImportFrom)):
                    self._process_py_import(module_name, item)
                elif isinstance(item, ast.ClassDef):
                    node.exports.append(f"class {item.name}")
                elif isinstance(item, ast.FunctionDef):
                    node.exports.append(f"func {item.name}")
        except SyntaxError:
            # Fallback to simple regex if AST fails
            imports = re.findall(r"^import\s+([\w\.]+)", content, re.M)
            from_imports = re.findall(r"^from\s+([\w\.]+)\s+import", content, re.M)
            for imp in imports + from_imports:
                self.edges.append(Edge(source=module_name, target=imp, kind="dependency"))

        return node

    def _process_py_import(self, source: str, item: Any):
        if isinstance(item, ast.Import):
            for name in item.names:
                self.edges.append(Edge(source=source, target=name.name, kind="import"))
        elif isinstance(item, ast.ImportFrom):
            if item.module:
                target = item.module
                # Handle relative imports
                if item.level > 0:
                    source_parts = source.split(".")
                    # item.level 1 = current dir, 2 = parent, etc.
                    target = ".".join(source_parts[:-(item.level-1)]) + "." + item.module
                self.edges.append(Edge(source=source, target=target, kind="import_from"))

    def scan(self) -> ArchitectureGraph:
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    python_files.append(Path(root) / f)

        # First pass: identify all internal modules
        for f in python_files:
            self.internal_modules.add(self._get_module_name(f))

        # Second pass: scan contents
        for f in python_files:
            node = self.scan_python_file(f)
            self.nodes[node.id] = node

        # Filter edges: only keep internal dependencies, or mark external
        final_edges = []
        for edge in self.edges:
            # Clean up target names (e.g. submodule imports)
            target = edge.target
            match = False
            # Check if it matches any internal module prefix
            for internal in sorted(self.internal_modules, key=len, reverse=True):
                if target == internal or target.startswith(internal + "."):
                    edge.target = internal
                    match = True
                    break
            
            if match:
                final_edges.append(edge)
            else:
                # Optional: track external dependencies
                edge.kind = "external"
                # For now we only visualize internal graph for clarity
                # final_edges.append(edge)

        # Deduplicate edges
        seen_edges = set()
        unique_edges = []
        for e in final_edges:
            key = (e.source, e.target)
            if key not in seen_edges and e.source != e.target:
                unique_edges.append(e)
                seen_edges.add(key)

        return ArchitectureGraph(
            nodes=list(self.nodes.values()),
            edges=unique_edges,
            root_path=str(self.root_dir)
        )

def scan_directory(path: str) -> ArchitectureGraph:
    scanner = CodeScanner(path)
    return scanner.scan()
