from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
import json

@dataclass
class Node:
    id: str
    label: str
    path: str
    kind: str = "module"
    layer: str = "Core"
    loc: int = 0
    exports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "path": self.path,
            "kind": self.kind,
            "layer": self.layer,
            "loc": self.loc,
            "exports": self.exports,
            "metadata": self.metadata
        }

@dataclass
class Edge:
    source: str
    target: str
    kind: str = "import"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind
        }

class ArchitectureGraph:
    def __init__(self, nodes: List[Node], edges: List[Edge], root_path: str = ""):
        self.nodes = {n.id: n for n in nodes}
        self.edges = edges
        self.root_path = root_path

    def get_layers(self) -> Dict[str, List[Node]]:
        layers: Dict[str, List[Node]] = {}
        for node in self.nodes.values():
            layers.setdefault(node.layer, []).append(node)
        return layers

    def in_degrees(self) -> Dict[str, int]:
        degrees = {nid: 0 for nid in self.nodes}
        for e in self.edges:
            if e.target in degrees:
                degrees[e.target] += 1
        return degrees

    def out_degrees(self) -> Dict[str, int]:
        degrees = {nid: 0 for nid in self.nodes}
        for e in self.edges:
            if e.source in degrees:
                degrees[e.source] += 1
        return degrees

    def detect_cycles(self) -> List[List[str]]:
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        for e in self.edges:
            if e.source in adj and e.target in adj:
                adj[e.source].append(e.target)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    idx = path.index(neighbor)
                    cycles.append(path[idx:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for nid in self.nodes:
            if nid not in visited:
                dfs(nid, [])

        return cycles

    def summary(self) -> Dict[str, Any]:
        in_deg = self.in_degrees()
        out_deg = self.out_degrees()
        total_loc = sum(n.loc for n in self.nodes.values())
        layers = self.get_layers()
        cycles = self.detect_cycles()

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_loc": total_loc,
            "layer_distribution": {k: len(v) for k, v in layers.items()},
            "cycles_count": len(cycles),
            "cycles": cycles,
            "hotspots": sorted(
                [{"id": nid, "dependents": in_deg[nid], "dependencies": out_deg[nid]} for nid in self.nodes],
                key=lambda x: (x["dependents"], x["dependencies"]),
                reverse=True
            )[:5]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps({
            "root_path": self.root_path,
            "summary": self.summary(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges]
        }, indent=indent)
