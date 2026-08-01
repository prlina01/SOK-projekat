import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
for package in (
    "api",
    "platform",
    "plugins/csv_data_source",
    "plugins/json_data_source",
    "plugins/simple_visualizer",
    "plugins/block_visualizer",
):
    sys.path.insert(0, str(PROJECT / package))

from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph_block_visualizer.plugin_main import BlockVisualizer
from graph_csv_source.plugin_main import CsvDataSourcePlugin
from graph_json_source.plugin_main import JsonDataSourcePlugin
from graph_simple_visualizer.plugin_main import SimpleVisualizer
from service.use_cases.graph_search_filter import GraphSearchFilter
from service.use_cases.tree_view import TreeView
from service.use_cases.workspace import Workspace


class DataSourceRegressionTests(unittest.TestCase):
    def test_all_demonstration_graphs_have_expected_cycle_state(self):
        csv_root = PROJECT / "plugins/csv_data_source/csv_data"
        json_root = PROJECT / "plugins/json_data_source/json_data"

        csv_cyclic = CsvDataSourcePlugin().load(source_path=csv_root / "graph_cyclic")
        csv_acyclic = CsvDataSourcePlugin().load(source_path=csv_root / "graph_acyclic")
        json_cyclic = JsonDataSourcePlugin().load(source_path=json_root / "cyclic_directed.json")
        json_acyclic = JsonDataSourcePlugin().load(source_path=json_root / "acyclic_undirected.json")

        self.assertTrue(csv_cyclic.cyclic)
        self.assertFalse(csv_acyclic.cyclic)
        self.assertTrue(json_cyclic.cyclic)
        self.assertFalse(json_acyclic.cyclic)
        self.assertFalse(csv_cyclic.directed)

    def test_generic_json_builds_reference_cycle_and_typed_values(self):
        graph = JsonDataSourcePlugin()
        payload = (
            '{"@id":"parent","created":"2026-07-31",'
            '"children":[{"@id":"child","age":"12","parent":"parent"}]}'
        )
        with tempfile.NamedTemporaryFile("w", suffix=".json") as source:
            source.write(payload)
            source.flush()
            loaded = graph.load(source_path=source.name)

        self.assertTrue(loaded.cyclic)
        self.assertEqual(loaded.nodes[1].data["age"], 12)
        self.assertEqual(loaded.nodes[0].data["created"], date(2026, 7, 31))

    def test_generic_csv_without_id_creates_row_nodes(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv") as source:
            source.write("name,score\nAlice,3.5\nBob,4\n")
            source.flush()
            loaded = CsvDataSourcePlugin().load(source_path=source.name)

        self.assertEqual([node.index for node in loaded.nodes], ["row-1", "row-2"])
        self.assertEqual(loaded.nodes[0].data["score"], 3.5)


class QueryAndCliRegressionTests(unittest.TestCase):
    def setUp(self):
        self.graph = Graph(
            nodes=[
                Node({"name": "Alice", "age": 31}, 1),
                Node({"name": "Bob", "age": 20}, 2),
            ],
            edges=[],
            cyclic=False,
            directed=True,
        )

    def test_search_and_filter_are_successive(self):
        queries = GraphSearchFilter()
        queries.set_source_graph(self.graph)
        self.assertEqual(len(queries.filter("age", "!=", "20").nodes), 1)
        self.assertEqual(len(queries.search("alice").nodes), 1)
        self.assertEqual(len(queries.filter("age", ">", "30").nodes), 1)

    def test_filter_rejects_wrong_value_type(self):
        queries = GraphSearchFilter()
        queries.set_source_graph(self.graph)
        with self.assertRaises(ValueError):
            queries.filter("age", ">", "old")

    def test_cli_edits_edges_and_clears_graph(self):
        workspace = Workspace(self.graph)
        workspace.cli.execute("create_edge id=e1 n1=1 n2=2 weight=2.5")
        workspace.cli.execute("edit_edge id=e1 weight=3.25")
        self.assertEqual(workspace.graph.edges[0].data["weight"], 3.25)
        workspace.cli.execute("delete_edge n1=1 n2=2")
        workspace.cli.execute("clear_graph")
        self.assertFalse(workspace.graph.nodes)


class VisualizerRegressionTests(unittest.TestCase):
    def test_tree_view_serializes_date_values(self):
        graph = Graph(nodes=[Node({"created": date(2026, 8, 1)}, 1)], edges=[])
        result = TreeView(graph).render(workspace_id="test")
        self.assertIn("2026-08-01", result)

    def test_plugins_return_html_without_core_dependency(self):
        graph = Graph(nodes=[Node({"name": "Alice"}, 1)], edges=[])
        for visualizer in (SimpleVisualizer(), BlockVisualizer()):
            result = visualizer.visualize(graph, workspace_id="test")
            self.assertIsInstance(result, str)
            self.assertIn("visualization-plugin-output", result)
            self.assertIn("data-visualization-model", result)


if __name__ == "__main__":
    unittest.main()
