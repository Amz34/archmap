import html
import json
import math
from typing import Dict, List, Tuple
from archmap.graph import ArchitectureGraph, Node

def render_mermaid(graph: ArchitectureGraph, title: str = "Codebase Architecture") -> str:
    lines = [
        "%%{init: {'theme': 'dark', 'themeVariables': { 'fontFamily': 'ui-sans-serif, system-ui, sans-serif' }}}%%",
        f"flowchart TB",
        f"    %% {title}"
    ]
    
    layers = graph.get_layers()
    layer_colors = {
        "CLI / UI": "#f59e0b",
        "Service / Logic": "#3b82f6",
        "Data / Model": "#10b981",
        "Utils / Shared": "#8b5cf6",
        "Test": "#64748b",
        "Core / App": "#06b6d4"
    }

    subgraph_idx = 0
    for layer_name, nodes in layers.items():
        clean_layer = "".join(c for c in layer_name if c.isalnum())
        subgraph_idx += 1
        lines.append(f"    subgraph SG_{clean_layer}[\"{layer_name}\"]")
        for node in nodes:
            safe_id = "".join(c if c.isalnum() else "_" for c in node.id)
            label = f"<b>{html.escape(node.label)}</b><br/><small>{node.loc} LOC</small>"
            lines.append(f"        {safe_id}[\"{label}\"]")
        lines.append("    end")

    lines.append("")
    for edge in graph.edges:
        s_id = "".join(c if c.isalnum() else "_" for c in edge.source)
        t_id = "".join(c if c.isalnum() else "_" for c in edge.target)
        if edge.source in graph.nodes and edge.target in graph.nodes:
            lines.append(f"    {s_id} --> {t_id}")

    return "\n".join(lines)


def render_svg(graph: ArchitectureGraph, width: int = 1200, height: int = 800) -> str:
    layers = graph.get_layers()
    layer_names = ["CLI / UI", "Service / Logic", "Core / App", "Data / Model", "Utils / Shared", "Test"]
    ordered_layers = [l for l in layer_names if l in layers] + [l for l in layers if l not in layer_names]

    layer_colors = {
        "CLI / UI": ("#fbbf24", "#78350f", "#1e1b18"),
        "Service / Logic": ("#60a5fa", "#1e3a8a", "#172554"),
        "Core / App": ("#22d3ee", "#164e63", "#083344"),
        "Data / Model": ("#34d399", "#064e3b", "#022c22"),
        "Utils / Shared": ("#c084fc", "#581c87", "#2e1065"),
        "Test": ("#94a3b8", "#334155", "#0f172a")
    }

    # Position calculations
    node_positions: Dict[str, Tuple[float, float, float, float]] = {}
    
    total_layers = max(1, len(ordered_layers))
    layer_height = (height - 140) / total_layers
    
    svg_elements: List[str] = []
    
    # Background
    svg_elements.append(f'<rect width="{width}" height="{height}" fill="#0f172a" rx="16"/>')
    svg_elements.append(f'<text x="40" y="55" font-family="system-ui, sans-serif" font-size="24" font-weight="700" fill="#f8fafc">Architecture Map</text>')
    svg_elements.append(f'<text x="40" y="80" font-family="system-ui, sans-serif" font-size="14" fill="#94a3b8">{len(graph.nodes)} Modules | {len(graph.edges)} Dependencies | {sum(n.loc for n in graph.nodes.values())} Total LOC</text>')

    for l_idx, layer in enumerate(ordered_layers):
        nodes = layers[layer]
        col_accent, col_border, col_bg = layer_colors.get(layer, ("#94a3b8", "#334155", "#1e293b"))
        y_base = 110 + l_idx * layer_height
        
        # Layer backdrop
        svg_elements.append(f'<rect x="30" y="{y_base}" width="{width - 60}" height="{layer_height - 15}" rx="10" fill="{col_bg}" fill-opacity="0.35" stroke="{col_border}" stroke-width="1.5" stroke-dasharray="4 4"/>')
        svg_elements.append(f'<text x="45" y="{y_base + 24}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="{col_accent}" text-transform="uppercase" letter-spacing="1">{html.escape(layer)}</text>')

        node_width = 170
        node_h = 50
        spacing = 20
        count = len(nodes)
        total_w = count * node_width + max(0, count - 1) * spacing
        start_x = max(180, (width - total_w) / 2) if total_w < (width - 220) else 180

        for n_idx, node in enumerate(nodes):
            x = start_x + n_idx * (node_width + spacing)
            if x + node_width > width - 40:
                x = 180 + (n_idx % 4) * (node_width + spacing)
            y = y_base + (layer_height - 15 - node_h) / 2 + 5
            node_positions[node.id] = (x, y, node_width, node_h)

            svg_elements.append(f'<g class="node" id="node-{node.id}">')
            svg_elements.append(f'<rect x="{x}" y="{y}" width="{node_width}" height="{node_h}" rx="8" fill="#1e293b" stroke="{col_accent}" stroke-width="1.5"/>')
            svg_elements.append(f'<text x="{x + 12}" y="{y + 22}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#f1f5f9">{html.escape(node.label[:18])}</text>')
            svg_elements.append(f'<text x="{x + 12}" y="{y + 38}" font-family="system-ui, sans-serif" font-size="11" fill="#94a3b8">{node.loc} LOC</text>')
            svg_elements.append('</g>')

    # Defs for marker arrows
    marker = """
    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
        </marker>
    </defs>
    """
    svg_elements.insert(1, marker)

    # Draw edges
    for edge in graph.edges:
        if edge.source in node_positions and edge.target in node_positions:
            sx, sy, sw, sh = node_positions[edge.source]
            tx, ty, tw, th = node_positions[edge.target]
            
            # Start from bottom center of source, end at top center of target
            start_x = sx + sw / 2
            start_y = sy + sh
            end_x = tx + tw / 2
            end_y = ty

            if start_y > end_y:
                # Reverse edge: draw side curve
                start_x = sx + sw
                start_y = sy + sh / 2
                end_x = tx + tw
                end_y = ty + th / 2
                mid_x = max(start_x, end_x) + 40
                path_d = f"M {start_x} {start_y} C {mid_x} {start_y}, {mid_x} {end_y}, {end_x} {end_y}"
            else:
                control_y = (start_y + end_y) / 2
                path_d = f"M {start_x} {start_y} C {start_x} {control_y}, {end_x} {control_y}, {end_x} {end_y}"

            svg_elements.append(f'<path d="{path_d}" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-opacity="0.65" marker-end="url(#arrow)"/>')

    content = "\n".join(svg_elements)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">\n{content}\n</svg>'


def render_html(graph: ArchitectureGraph, title: str = "Codebase Architecture Dashboard") -> str:
    mermaid_code = render_mermaid(graph, title=title)
    svg_code = render_svg(graph)
    summary = graph.summary()
    summary_json = json.dumps(summary, indent=2)
    nodes_json = json.dumps([n.to_dict() for n in graph.nodes.values()], indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        :root {{
            --bg-main: #090d16;
            --bg-card: #111827;
            --border-color: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .brand h1 {{ font-size: 18px; font-weight: 700; letter-spacing: -0.02em; }}
        .badge {{
            background: #1e293b;
            border: 1px solid #334155;
            color: var(--accent);
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .stats-bar {{
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .stats-bar span strong {{ color: var(--text-primary); }}
        .main-layout {{
            display: flex;
            flex: 1;
            height: calc(100vh - 65px);
            overflow: hidden;
        }}
        .sidebar {{
            width: 340px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}
        .viewport {{
            flex: 1;
            padding: 24px;
            overflow: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .search-box {{
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        .search-input {{
            width: 100%;
            background: #0f172a;
            border: 1px solid #334155;
            color: #fff;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
        }}
        .search-input:focus {{ border-color: var(--accent); }}
        .module-list {{ list-style: none; padding: 8px; }}
        .module-item {{
            padding: 10px 14px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            margin-bottom: 4px;
            transition: background 0.15s;
        }}
        .module-item:hover, .module-item.active {{
            background: #1f2937;
        }}
        .view-controls {{
            margin-bottom: 16px;
            display: flex;
            gap: 10px;
            width: 100%;
            max-width: 1200px;
            justify-content: flex-end;
        }}
        .btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #fff;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
        }}
        .btn.active {{ background: var(--accent); color: #0f172a; font-weight: 600; border-color: var(--accent); }}
        .diagram-container {{
            width: 100%;
            max-width: 1200px;
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);
        }}
        pre.code-view {{
            background: #0b0f19;
            padding: 16px;
            border-radius: 8px;
            font-family: ui-monospace, monospace;
            font-size: 12px;
            line-height: 1.5;
            color: #38bdf8;
            overflow-x: auto;
            display: none;
        }}
        .info-panel {{
            padding: 16px;
            border-top: 1px solid var(--border-color);
            background: #0b1120;
            font-size: 13px;
        }}
        .info-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 8px; font-weight: 700; }}
        .badge-tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin: 2px 2px 2px 0;
            background: #334155;
            color: #cbd5e1;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <h1>archmap</h1>
            <span class="badge">v1.0.0</span>
        </div>
        <div class="stats-bar">
            <span>Modules: <strong>{summary["total_nodes"]}</strong></span>
            <span>Dependencies: <strong>{summary["total_edges"]}</strong></span>
            <span>Lines of Code: <strong>{summary["total_loc"]}</strong></span>
            <span>Cycles: <strong>{summary["cycles_count"]}</strong></span>
        </div>
    </header>

    <div class="main-layout">
        <aside class="sidebar">
            <div class="search-box">
                <input type="text" id="filterInput" class="search-input" placeholder="Search modules...">
            </div>
            <ul class="module-list" id="moduleList"></ul>
            <div class="info-panel" id="inspectorPanel">
                <div class="info-title">Module Inspector</div>
                <p id="inspectText" style="color: var(--text-secondary); font-size: 12px;">Select any node to inspect exported symbols, layer placement, and dependencies.</p>
            </div>
        </aside>

        <main class="viewport">
            <div class="view-controls">
                <button class="btn active" id="btnSvg" onclick="switchView('svg')">Visual Map</button>
                <button class="btn" id="btnMermaid" onclick="switchView('mermaid')">Mermaid Spec</button>
                <button class="btn" id="btnJson" onclick="switchView('json')">Graph JSON</button>
            </div>

            <div class="diagram-container" id="svgContainer">
                {svg_code}
            </div>

            <pre class="code-view" id="mermaidContainer">{html.escape(mermaid_code)}</pre>
            <pre class="code-view" id="jsonContainer">{html.escape(graph.to_json())}</pre>
        </main>
    </div>

    <script>
        const nodesData = {nodes_json};
        
        function switchView(view) {{
            document.getElementById('svgContainer').style.display = view === 'svg' ? 'block' : 'none';
            document.getElementById('mermaidContainer').style.display = view === 'mermaid' ? 'block' : 'none';
            document.getElementById('jsonContainer').style.display = view === 'json' ? 'block' : 'none';
            document.getElementById('btnSvg').className = 'btn ' + (view === 'svg' ? 'active' : '');
            document.getElementById('btnMermaid').className = 'btn ' + (view === 'mermaid' ? 'active' : '');
            document.getElementById('btnJson').className = 'btn ' + (view === 'json' ? 'active' : '');
        }}

        const listEl = document.getElementById('moduleList');
        const filterInput = document.getElementById('filterInput');

        function renderList(filter = '') {{
            listEl.textContent = '';
            nodesData
                .filter(n => n.id.toLowerCase().includes(filter.toLowerCase()) || n.label.toLowerCase().includes(filter.toLowerCase()))
                .forEach(n => {{
                    const li = document.createElement('li');
                    li.className = 'module-item';
                    
                    const leftSpan = document.createElement('span');
                    const strong = document.createElement('strong');
                    strong.textContent = n.label;
                    const layerSmall = document.createElement('small');
                    layerSmall.style.color = '#64748b';
                    layerSmall.textContent = ' ' + n.layer;
                    leftSpan.appendChild(strong);
                    leftSpan.appendChild(layerSmall);

                    const rightSpan = document.createElement('span');
                    rightSpan.style.color = '#94a3b8';
                    rightSpan.textContent = n.loc + ' LOC';

                    li.appendChild(leftSpan);
                    li.appendChild(rightSpan);
                    li.onclick = () => selectNode(n);
                    listEl.appendChild(li);
                }});
        }}

        function selectNode(node) {{
            const p = document.getElementById('inspectorPanel');
            p.textContent = '';

            const title = document.createElement('div');
            title.className = 'info-title';
            title.textContent = 'Module Details';

            const idDiv = document.createElement('div');
            idDiv.style.fontWeight = '700';
            idDiv.style.fontSize = '15px';
            idDiv.style.marginBottom = '4px';
            idDiv.textContent = node.id;

            const pathDiv = document.createElement('div');
            pathDiv.style.fontSize = '12px';
            pathDiv.style.color = '#94a3b8';
            pathDiv.style.marginBottom = '12px';
            pathDiv.textContent = node.path;

            const layerDiv = document.createElement('div');
            layerDiv.style.fontSize = '12px';
            layerDiv.style.marginBottom = '8px';
            layerDiv.textContent = 'Layer: ' + node.layer;

            const locDiv = document.createElement('div');
            locDiv.style.fontSize = '12px';
            locDiv.style.marginBottom = '8px';
            locDiv.textContent = 'LOC: ' + node.loc;

            const exportsTitle = document.createElement('div');
            exportsTitle.className = 'info-title';
            exportsTitle.style.marginTop = '12px';
            exportsTitle.textContent = 'Exports';

            const exportsDiv = document.createElement('div');
            if (node.exports && node.exports.length > 0) {{
                node.exports.forEach(exp => {{
                    const tag = document.createElement('span');
                    tag.className = 'badge-tag';
                    tag.textContent = exp;
                    exportsDiv.appendChild(tag);
                }});
            }} else {{
                const empty = document.createElement('span');
                empty.style.color = '#64748b';
                empty.textContent = 'None detected';
                exportsDiv.appendChild(empty);
            }}

            p.appendChild(title);
            p.appendChild(idDiv);
            p.appendChild(pathDiv);
            p.appendChild(layerDiv);
            p.appendChild(locDiv);
            p.appendChild(exportsTitle);
            p.appendChild(exportsDiv);
        }}

        filterInput.addEventListener('input', (e) => renderList(e.target.value));
        renderList();
    </script>
</body>
</html>
"""
