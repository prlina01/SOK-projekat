import html
import json
from datetime import date, datetime


def graph_data(graph):
    """Convert a Graph into the browser-neutral visualization payload."""
    return {
        "nodes": [
            {"id": str(node.index), "data": node.data or {}}
            for node in (graph.nodes or [])
        ],
        "edges": [
            {
                "source": str(edge.node1.index),
                "target": str(edge.node2.index),
                "id": edge.index,
                "data": edge.data or {},
            }
            for edge in (graph.edges or [])
            if edge.node1 is not None and edge.node2 is not None
        ],
        "directed": bool(graph.directed),
        "cyclic": bool(graph.cyclic),
    }


def visualization_html(plugin_id, graph, workspace_id, options):
    """Return the HTML string required by the VisualizationPlugin contract."""
    model = {
        "plugin_id": plugin_id,
        "workspace_id": str(workspace_id),
        "graph": graph_data(graph),
        "options": options,
    }
    payload = json.dumps(
        model,
        ensure_ascii=False,
        default=lambda value: value.isoformat()
        if isinstance(value, (date, datetime))
        else str(value),
    )
    return (
        '<div class="visualization-plugin-output" '
        f'data-visualization-model="{html.escape(payload, quote=True)}"></div>'
    )
