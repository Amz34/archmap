import unittest
import tempfile
import os
import shutil
import json
from pathlib import Path

from archmap.scanner import CodeScanner, scan_directory
from archmap.graph import ArchitectureGraph, Node, Edge
from archmap.renderers import render_mermaid, render_svg, render_html
from archmap.cli import main, build_parser

class TestArchmap(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample project structure
        # app/
        #   cli.py -> imports service
        #   service.py -> imports model
        #   model.py
        #   util.py
        app_dir = Path(self.test_dir) / "sample_pkg"
        app_dir.mkdir(parents=True)
        
        with open(app_dir / "__init__.py", "w") as f:
            f.write("# init\n")

        with open(app_dir / "cli.py", "w") as f:
            f.write("from sample_pkg.service import run_service\n\ndef main():\n    run_service()\n")

        with open(app_dir / "service.py", "w") as f:
            f.write("from sample_pkg.model import Item\n\ndef run_service():\n    item = Item('demo')\n    return item\n")

        with open(app_dir / "model.py", "w") as f:
            f.write("class Item:\n    def __init__(self, name):\n        self.name = name\n")

        with open(app_dir / "util.py", "w") as f:
            f.write("def helper():\n    return 42\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scanner_discovers_modules_and_dependencies(self):
        graph = scan_directory(self.test_dir)
        self.assertGreaterEqual(len(graph.nodes), 4)
        
        # Check node IDs
        ids = list(graph.nodes.keys())
        self.assertTrue(any("sample_pkg.cli" in i for i in ids))
        self.assertTrue(any("sample_pkg.service" in i for i in ids))
        self.assertTrue(any("sample_pkg.model" in i for i in ids))
        
        # Check layers
        cli_node = [n for n in graph.nodes.values() if "cli" in n.id][0]
        self.assertEqual(cli_node.layer, "CLI / UI")

        model_node = [n for n in graph.nodes.values() if "model" in n.id][0]
        self.assertEqual(model_node.layer, "Data / Model")

        # Check dependency edge from cli -> service
        edges = [(e.source, e.target) for e in graph.edges]
        self.assertTrue(any("sample_pkg.cli" in s and "sample_pkg.service" in t for s, t in edges))

    def test_graph_metrics_and_summary(self):
        n1 = Node(id="pkg.a", label="a", path="pkg/a.py", layer="Core", loc=50)
        n2 = Node(id="pkg.b", label="b", path="pkg/b.py", layer="Service / Logic", loc=100)
        e1 = Edge(source="pkg.a", target="pkg.b")
        
        graph = ArchitectureGraph(nodes=[n1, n2], edges=[e1])
        summary = graph.summary()
        
        self.assertEqual(summary["total_nodes"], 2)
        self.assertEqual(summary["total_edges"], 1)
        self.assertEqual(summary["total_loc"], 150)
        self.assertEqual(summary["cycles_count"], 0)
        self.assertIn("Core", summary["layer_distribution"])

    def test_cycle_detection(self):
        n1 = Node(id="a", label="a", path="a.py")
        n2 = Node(id="b", label="b", path="b.py")
        e1 = Edge(source="a", target="b")
        e2 = Edge(source="b", target="a")
        
        graph = ArchitectureGraph(nodes=[n1, n2], edges=[e1, e2])
        cycles = graph.detect_cycles()
        self.assertGreater(len(cycles), 0)

    def test_renderers(self):
        graph = scan_directory(self.test_dir)
        
        # Mermaid
        mermaid_out = render_mermaid(graph)
        self.assertIn("flowchart TB", mermaid_out)
        self.assertIn("subgraph", mermaid_out)

        # SVG
        svg_out = render_svg(graph)
        self.assertTrue(svg_out.startswith("<svg"))
        self.assertTrue(svg_out.endswith("</svg>"))
        self.assertIn("Architecture Map", svg_out)

        # HTML
        html_out = render_html(graph)
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("archmap", html_out)
        self.assertIn("Module Inspector", html_out)

    def test_cli_execution(self):
        # Summary command
        rc = main(["summary", self.test_dir])
        self.assertEqual(rc, 0)

        # Scan to SVG
        svg_file = os.path.join(self.test_dir, "test.svg")
        rc = main(["scan", self.test_dir, "-f", "svg", "-o", svg_file])
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(svg_file))

        # Scan to HTML
        html_file = os.path.join(self.test_dir, "test.html")
        rc = main(["scan", self.test_dir, "-f", "html", "-o", html_file])
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(html_file))

if __name__ == "__main__":
    unittest.main()
