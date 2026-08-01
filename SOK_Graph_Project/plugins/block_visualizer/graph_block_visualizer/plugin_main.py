from graph.api.services.plugin import VisualizationPlugin
from graph.api.model.graph import Graph
from graph.api.services.visualization import visualization_html


class BlockVisualizer(VisualizationPlugin):
    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> str:
        workspace_id = kwargs.get("workspace_id", "default-workspace")
        return visualization_html(
            self.identifier(), graph, workspace_id,
            {
                "width": kwargs.get("width", 900),
                "height": kwargs.get("height", 550),
                "link_distance": kwargs.get("link_distance", 200),
                "charge_strength": kwargs.get("charge_strength", -3000),
                "container_id": kwargs.get("container_id", f"block-visualizer-{workspace_id}"),
                "node_radius": 80
            }
        )
