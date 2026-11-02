# archmap

Lightweight codebase architecture visualizer and diagram generator with zero external dependencies.

![Architecture Overview](assets/archmap-overview.jpg)

## Why archmap?

Understanding the structure and component relationships of a software project usually requires complex tooling, heavy node dependencies, or paid SaaS diagrams. `archmap` delivers an immediate, dependency-free architecture diagram generator built exclusively with the Python standard library.

It parses module hierarchies, scans dependency imports via AST analysis, categorizes architectural layers, detects cyclic coupling, and exports standalone visual artifacts: interactive HTML dashboards, clean SVG vector diagrams, or Mermaid flowchart specifications.

## Features

- **Zero External Dependencies**: Runs entirely on Python 3.10+ standard library (`ast`, `argparse`, `json`, `html`, `re`).
- **Multiple Output Formats**:
  - **Interactive HTML**: Self-contained single-page dashboard with zoom/pan, search filtering, and module inspector panel.
  - **Standalone SVG**: Scalable vector diagram with color-coded architectural layers and routing arrows.
  - **Mermaid Flowchart**: Markdown-compatible diagram syntax ready for GitHub documentation.
  - **Structured JSON**: Machine-readable node and edge graph schema with coupling statistics.
- **Automated Layer Classification**: Automatically categorizes files into presentation (`CLI / UI`), business logic (`Service / Logic`), data models (`Data / Model`), core components (`Core / App`), shared utilities (`Utils / Shared`), and testing (`Test`).
- **Architectural Health Analysis**: Identifies circular dependency cycles and surfaces hotspot modules with high incoming or outgoing couplings.

## Quickstart

### Installation

Clone the repository and run directly:

```bash
git clone https://github.com/Amz34/archmap.git
cd archmap
```

No external `pip` dependencies are required.

### Generate an Interactive HTML Diagram

Scan any project directory to produce a standalone HTML report:

```bash
python3 -m archmap scan /path/to/project -f html -o archmap.html
```

Open `archmap.html` in any web browser to view the interactive map, inspect module details, and search across components.

### Generate Standalone SVG or Mermaid

```bash
# Standalone scalable SVG vector graphic
python3 -m archmap scan /path/to/project -f svg -o architecture.svg

# Mermaid flowchart to stdout (ideal for embedding in README files)
python3 -m archmap scan /path/to/project -f mermaid
```

### Inspect Architecture Metrics

Print module counts, layer breakdown, hotspot couplings, and circular dependency checks directly in your terminal:

```bash
python3 -m archmap summary /path/to/project
```

Example terminal output:

```text
=== Architecture Summary: /path/to/project ===
Total Modules : 18
Dependencies  : 24
Total LOC     : 2450
Cycles Count  : 0

Layer Distribution:
  • CLI / UI           : 2 modules
  • Service / Logic    : 6 modules
  • Core / App         : 4 modules
  • Data / Model       : 3 modules
  • Utils / Shared     : 3 modules

Dependency Graph : Clean (No circular dependencies detected)

Top Architectural Hotspots (by incoming/outgoing couplings):
  • app.core.config          : 8 dependents | 0 dependencies
  • app.services.engine      : 4 dependents | 3 dependencies
  • app.models.entities      : 5 dependents | 0 dependencies
```

## How It Works

1. **AST AST Traversal**: `archmap` walks target directories, skipping build artifacts and virtual environments, and parses Python files into Abstract Syntax Trees.
2. **Dependency Resolution**: It resolves `import` and `from ... import` statements against internal project modules while resolving relative module paths.
3. **Graph Construction**: Modules become nodes categorized by heuristics; dependencies form a directed acyclic graph (DAG).
4. **Analysis**: In-degrees, out-degrees, and Tarjan/DFS cycles are calculated to detect architectural coupling.
5. **Rendering**: The graph is formatted into responsive vector SVG, Mermaid definitions, or a single-file zero-dependency HTML interface.

## Limitations

- **Language Scope**: Full AST-based import analysis is specialized for Python codebases. Basic file hierarchy and regex import scanning are supported for JavaScript and TypeScript.
- **Dynamic Imports**: Imports evaluated at runtime via `importlib.import_module` or `__import__` with dynamic strings cannot be discovered statically.
- **Graph Layout**: The standalone SVG renderer uses hierarchical layer positioning optimized for standard layered architectures up to ~150 modules. Larger codebases are best analyzed using the interactive HTML search or JSON export.

## Testing

Run the comprehensive unit test suite:

```bash
make test
```

## License

MIT License. Copyright (c) 2026 Amz34.

---

Part of [my always-on agent stack](https://github.com/Amz34) · [Awesome Agent Infrastructure](https://github.com/Amz34/awesome-agent-infrastructure) (135 live-checked building blocks).
