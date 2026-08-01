from __future__ import annotations

from datetime import date, datetime

from graph.api.model.graph import Graph


class GraphSearchFilter:
	def __init__(self):
		self._source_graph = Graph()
		self._filtered_graph = Graph()

	@property
	def filtered_graph(self) -> Graph:
		return self._filtered_graph

	def set_source_graph(self, graph: Graph) -> None:
		self._source_graph = graph if graph is not None else Graph()
		self._filtered_graph = self._clone_graph(self._source_graph)

	def clear_filters(self, graph: Graph) -> Graph:
		self.set_source_graph(graph)
		return self.filtered_graph

	def filter(self, attribute: str, operator: str, value: str) -> Graph:
		attribute = (attribute or "").strip()

		if not attribute:
			self._filtered_graph = self._clone_graph(self._filtered_graph)
			return self.filtered_graph

		matched_nodes = []
		for node in self.filtered_graph.nodes:
			node_data = node.data if isinstance(node.data, dict) else {}
			if attribute not in node_data:
				continue

			node_value = node_data.get(attribute)
			if self._matches_operator(node_value, operator, value):
				matched_nodes.append(node)

		self._filtered_graph = self._build_subgraph(self.filtered_graph, matched_nodes)
		return self.filtered_graph

	def search(self, query: str) -> Graph:
		query = (query or "").strip().lower()

		if not query:
			self._filtered_graph = self._clone_graph(self.filtered_graph)
			return self.filtered_graph

		matched_nodes = []
		for node in self.filtered_graph.nodes:
			node_data = node.data if isinstance(node.data, dict) else {}
			if self._node_contains(node_data, query):
				matched_nodes.append(node)

		self._filtered_graph = self._build_subgraph(self.filtered_graph, matched_nodes)
		return self.filtered_graph

	def _build_subgraph(self, graph: Graph, nodes: list) -> Graph:
		node_ids = {str(node.index) for node in nodes}
		edges = []

		for edge in graph.edges:
			node1 = edge.node1
			node2 = edge.node2
			if node1 is None or node2 is None:
				continue

			if str(node1.index) in node_ids and str(node2.index) in node_ids:
				edges.append(edge)

		return Graph(
			nodes=list(nodes),
			edges=edges,
			cyclic=graph.cyclic,
			directed=graph.directed,
		)

	def _clone_graph(self, graph: Graph) -> Graph:
		if graph is None:
			return Graph()

		return Graph(
			nodes=list(graph.nodes or []),
			edges=list(graph.edges or []),
			cyclic=graph.cyclic,
			directed=graph.directed,
		)

	def _matches_operator(self, node_value, operator: str, expected_value: str) -> bool:
		operator = (operator or "=").strip()
		if operator not in {"=", "==", "!=", "<", "<=", ">", ">="}:
			raise ValueError(f"Unsupported filter operator: {operator}")

		expected = self._coerce_expected_value(node_value, expected_value)

		if operator in {"=", "=="}:
			return node_value == expected
		if operator == "!=":
			return node_value != expected
		if operator == "<":
			return node_value < expected
		if operator == "<=":
			return node_value <= expected
		if operator == ">":
			return node_value > expected
		return node_value >= expected

	def _coerce_expected_value(self, node_value, expected_value):
		try:
			if isinstance(node_value, bool):
				value = str(expected_value).strip().lower()
				if value not in {"true", "false"}:
					raise ValueError
				return value == "true"
			if isinstance(node_value, int):
				return int(expected_value)
			if isinstance(node_value, float):
				return float(expected_value)
			if isinstance(node_value, datetime):
				return datetime.fromisoformat(str(expected_value).replace("Z", "+00:00"))
			if isinstance(node_value, date):
				return date.fromisoformat(str(expected_value))
			if isinstance(node_value, str):
				return str(expected_value)
		except (TypeError, ValueError) as exc:
			raise ValueError(
				f"Value '{expected_value}' does not match attribute type "
				f"{type(node_value).__name__}"
			) from exc

		raise ValueError(
			f"Filtering values of type {type(node_value).__name__} is not supported"
		)

	def _node_contains(self, node_data: dict, query: str) -> bool:
		for key, value in node_data.items():
			if query in str(key).lower() or query in str(value).lower():
				return True

		return False
