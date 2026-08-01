import json
import os
from collections import defaultdict
from datetime import date, datetime

from graph.api.model.node import Node
from graph.api.model.edge import Edge
from graph.api.model.graph import Graph


class DataSourceService:

    @staticmethod
    def parse_scalar(value):
        if not isinstance(value, str):
            return value

        text = value.strip()
        if text == "":
            return ""

        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none"}:
            return None

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            pass

        try:
            if "T" in text or " " in text:
                return datetime.fromisoformat(text.replace("Z", "+00:00"))
            return date.fromisoformat(text)
        except ValueError:
            return value

    @staticmethod
    def normalize_values(value):
        if isinstance(value, dict):
            return {
                key: DataSourceService.normalize_values(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [DataSourceService.normalize_values(item) for item in value]
        return DataSourceService.parse_scalar(value)

    # --------------------------------------------------
    # PATH VALIDATION
    # --------------------------------------------------

    @staticmethod
    def require_source_path(source_path):
        if not source_path:
            raise ValueError("source_path is required")
        return os.path.abspath(source_path)

    @staticmethod
    def require_existing_file(source_path, extension=None):
        source_path = DataSourceService.require_source_path(source_path)

        if not os.path.isfile(source_path):
            raise ValueError(f"File does not exist: {source_path}")

        if extension and not source_path.lower().endswith(extension.lower()):
            raise ValueError(f"Expected a {extension} file")

        return source_path

    @staticmethod
    def require_existing_directory(source_path):
        source_path = DataSourceService.require_source_path(source_path)

        if not os.path.isdir(source_path):
            raise ValueError(f"Directory does not exist: {source_path}")

        return source_path

    @staticmethod
    def require_files(directory, required_files):
        missing = [
            f for f in required_files
            if not os.path.isfile(os.path.join(directory, f))
        ]

        if missing:
            raise ValueError(
                f"Directory '{directory}' missing files: {', '.join(missing)}"
            )

        return {
            f: os.path.join(directory, f)
            for f in required_files
        }

    # --------------------------------------------------
    # JSON HELPERS
    # --------------------------------------------------

    @staticmethod
    def read_json(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json(file_path, payload):
        directory = os.path.dirname(file_path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                payload,
                f,
                indent=4,
                ensure_ascii=False,
                default=lambda value: value.isoformat()
                if isinstance(value, (date, datetime))
                else str(value)
            )

    # --------------------------------------------------
    # GRAPH BUILDING
    # --------------------------------------------------

    @staticmethod
    def build_graph(nodes, edges, directed=True):

        node_objects = []
        node_map = {}

        for node in nodes:
            node_obj = Node(
                index=node["index"],
                data=DataSourceService.normalize_values(node.get("data", {}))
            )
            node_objects.append(node_obj)
            node_map[node_obj.index] = node_obj

        edge_objects = []

        for edge in edges:
            if isinstance(edge, dict):
                source = edge.get("node1_index", edge.get("source"))
                target = edge.get("node2_index", edge.get("target"))
                edge_index = edge.get("index", edge.get("id"))
                edge_data = DataSourceService.normalize_values(edge.get("data", {}))
            else:
                source, target = edge
                edge_index = None
                edge_data = {}

            if source not in node_map:
                raise ValueError(f"Unknown node index: {source}")

            if target not in node_map:
                raise ValueError(f"Unknown node index: {target}")

            edge_objects.append(
                Edge(
                    node1=node_map[source],
                    node2=node_map[target],
                    index=edge_index,
                    data=edge_data
                )
            )

        cyclic = DataSourceService.detect_cycle(
            node_objects,
            edge_objects,
            directed
        )

        return Graph(
            nodes=node_objects,
            edges=edge_objects,
            directed=directed,
            cyclic=cyclic
        )

    # --------------------------------------------------
    # GRAPH SERIALIZATION
    # --------------------------------------------------

    @staticmethod
    def graph_to_dict(graph):

        return {
            "nodes": [
                {
                    "index": node.index,
                    "data": node.data or {}
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "index": edge.index,
                    "node1_index": edge.node1.index if edge.node1 else None,
                    "node2_index": edge.node2.index if edge.node2 else None,
                    "data": edge.data or {}
                }
                for edge in graph.edges
            ],
            "directed": graph.directed,
            "cyclic": graph.cyclic
        }

    @staticmethod
    def dict_to_graph(data):
        if not isinstance(data, dict):
            return DataSourceService.document_to_graph(data)

        if "nodes" not in data or "edges" not in data:
            return DataSourceService.document_to_graph(data)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        return DataSourceService.build_graph(
            nodes,
            edges,
            directed=data.get("directed", True)
        )

    @staticmethod
    def document_to_graph(document):
        """Map arbitrary nested JSON objects to nodes and relationships."""
        nodes = []
        edges = []
        object_ids = {}
        used_ids = set()

        def unique_index(value, path):
            candidate = str(value) if value not in (None, "") else path
            base = candidate
            suffix = 2
            while candidate in used_ids:
                candidate = f"{base}_{suffix}"
                suffix += 1
            used_ids.add(candidate)
            return candidate

        def collect(value, path="root"):
            if isinstance(value, dict):
                index = unique_index(value.get("@id", value.get("id")), path)
                object_ids[id(value)] = index
                scalar_data = {}
                for key, item in value.items():
                    if key in {"@id", "id"}:
                        continue
                    if isinstance(item, (dict, list)):
                        continue
                    scalar_data[key] = DataSourceService.parse_scalar(item)
                nodes.append({"index": index, "data": scalar_data})
                for key, item in value.items():
                    if isinstance(item, dict):
                        collect(item, f"{path}.{key}")
                    elif isinstance(item, list):
                        for position, child in enumerate(item):
                            if isinstance(child, dict):
                                collect(child, f"{path}.{key}[{position}]")
                return

            if isinstance(value, list):
                for position, item in enumerate(value):
                    if isinstance(item, (dict, list)):
                        collect(item, f"{path}[{position}]")

        collect(document)
        known_ids = {node["index"] for node in nodes}

        def connect(value):
            if isinstance(value, dict):
                source = object_ids[id(value)]
                for key, item in value.items():
                    if isinstance(item, dict):
                        edges.append((source, object_ids[id(item)]))
                        connect(item)
                    elif isinstance(item, list):
                        for child in item:
                            if isinstance(child, dict):
                                edges.append((source, object_ids[id(child)]))
                                connect(child)
                    elif key not in {"@id", "id"} and str(item) in known_ids:
                        edges.append((source, str(item)))
            elif isinstance(value, list):
                for item in value:
                    connect(item)

        connect(document)
        return DataSourceService.build_graph(nodes, edges, directed=True)

    # --------------------------------------------------
    # CYCLE DETECTION
    # --------------------------------------------------

    @staticmethod
    def detect_cycle(nodes, edges, directed=True):

        adjacency = defaultdict(list)

        for edge in edges:
            adjacency[edge.node1.index].append(edge.node2.index)

            if not directed:
                adjacency[edge.node2.index].append(edge.node1.index)

        visited = set()
        stack = set()

        def dfs(node, parent=None):

            visited.add(node)
            stack.add(node)

            for neighbor in adjacency[node]:

                if directed:

                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True

                    elif neighbor in stack:
                        return True

                else:

                    if neighbor not in visited:
                        if dfs(neighbor, node):
                            return True

                    elif neighbor != parent:
                        return True

            stack.remove(node)

            return False

        for node in nodes:

            if node.index not in visited:
                if dfs(node.index):
                    return True

        return False
