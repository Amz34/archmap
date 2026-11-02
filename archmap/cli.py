import argparse
import sys
import os
from archmap import __version__
from archmap.scanner import scan_directory
from archmap.renderers import render_html, render_svg, render_mermaid

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archmap",
        description="Lightweight codebase architecture visualizer and diagram generator."
    )
    parser.add_argument("--version", action="version", version=f"archmap {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a directory and generate architecture diagram")
    scan_parser.add_argument("path", nargs="?", default=".", help="Root directory of codebase to scan (default: .)")
    scan_parser.add_argument(
        "-f", "--format",
        choices=["html", "svg", "mermaid", "json"],
        default="html",
        help="Output diagram format (default: html)"
    )
    scan_parser.add_argument("-o", "--output", help="Output file path (default: stdout for mermaid/json, archmap.html/svg for html/svg)")
    scan_parser.add_argument("--title", default="Codebase Architecture", help="Diagram title")

    # summary command
    sum_parser = subparsers.add_parser("summary", help="Print tabular architectural complexity summary")
    sum_parser.add_argument("path", nargs="?", default=".", help="Root directory of codebase to scan (default: .)")

    return parser


def print_summary(summary: dict, path: str):
    print(f"\n=== Architecture Summary: {os.path.abspath(path)} ===")
    print(f"Total Modules : {summary['total_nodes']}")
    print(f"Dependencies  : {summary['total_edges']}")
    print(f"Total LOC     : {summary['total_loc']}")
    print(f"Cycles Count  : {summary['cycles_count']}")

    print("\nLayer Distribution:")
    for layer, count in summary['layer_distribution'].items():
        print(f"  • {layer:<18} : {count} modules")

    if summary['cycles']:
        print("\nDetected Dependency Cycles:")
        for cycle in summary['cycles']:
            print(f"  [!] {' -> '.join(cycle)}")
    else:
        print("\nDependency Graph : Clean (No circular dependencies detected)")

    if summary['hotspots']:
        print("\nTop Architectural Hotspots (by incoming/outgoing couplings):")
        for h in summary['hotspots']:
            print(f"  • {h['id']:<24} : {h['dependents']} dependents | {h['dependencies']} dependencies")
    print()


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "summary":
        graph = scan_directory(args.path)
        print_summary(graph.summary(), args.path)
        return 0

    if args.command == "scan":
        graph = scan_directory(args.path)
        fmt = args.format.lower()
        title = args.title

        if fmt == "html":
            rendered = render_html(graph, title=title)
            default_out = "archmap.html"
        elif fmt == "svg":
            rendered = render_svg(graph)
            default_out = "archmap.svg"
        elif fmt == "mermaid":
            rendered = render_mermaid(graph, title=title)
            default_out = None
        elif fmt == "json":
            rendered = graph.to_json()
            default_out = None
        else:
            sys.stderr.write(f"Unknown format: {fmt}\n")
            return 1

        out_path = args.output or default_out
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"Generated {fmt.upper()} diagram at: {os.path.abspath(out_path)}")
        else:
            print(rendered)

        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())
