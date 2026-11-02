"""archmap - Lightweight codebase architecture visualizer and diagram generator.

Zero-dependency tool to extract module dependency graphs, architectural layers,
and export standalone interactive HTML, clean SVG, or Mermaid diagrams.
"""

__version__ = "1.0.0"
__author__ = "Amz34"

from archmap.graph import ArchitectureGraph, Edge, Node
from archmap.scanner import scan_directory

__all__ = ["ArchitectureGraph", "Edge", "Node", "scan_directory", "__version__"]
