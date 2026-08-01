
from .edge import Edge
from .node import Node
from dataclasses import dataclass
from typing import Any

@dataclass
class Graph:
    """Shared graph model exchanged between the platform and every plugin.

    ``directed`` describes edge direction, while ``cyclic`` records whether
    the represented graph contains at least one cycle.
    """

    def __init__(
        self,
        nodes: list[Node] | None = None,
        edges: list[Edge] | None = None,
        cyclic: bool | None = None,
        directed: bool | None = None,
    ):
        self.nodes = nodes
        self.edges = edges
        self.cyclic = cyclic
        self.directed = directed

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = self._validateNodesList(value)

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = self._validateEdgesList(value)

    @property
    def cyclic(self):
        return self._cyclic

    @cyclic.setter
    def cyclic(self, value):
        self._cyclic = value

    @property
    def directed(self):
        return self._directed

    @directed.setter
    def directed(self, value):
        self._directed = value

    def addNode(self, node: Node) -> None:
        """Add a validated node to the graph."""
        self.nodes.append(self._validateNode(node))

    def addEdge(self, edge: Edge) -> None:
        """Add a validated edge to the graph."""
        self.edges.append(self._validateEdge(edge))

    def removeEdgeByNodes(self, node1: Node, node2: Node) -> None:
        """Remove the first edge connecting the supplied endpoints."""
        node1_id = self._getNodeId(node1)
        node2_id = self._getNodeId(node2)

        for idx, edge in enumerate(self.edges):
            edge_node1_id = self._getNodeId(edge.node1)
            edge_node2_id = self._getNodeId(edge.node2)

            direct_match = edge_node1_id == node1_id and edge_node2_id == node2_id
            reverse_match = edge_node1_id == node2_id and edge_node2_id == node1_id

            if direct_match or (not self.directed and reverse_match):
                del self.edges[idx]
                return

        raise ValueError("No edge found for the provided two nodes")

    def removeEdge(self, edge: Edge) -> None:
        """Remove an edge instance from the graph."""
        for idx, current_edge in enumerate(self.edges):
            if current_edge is edge:
                del self.edges[idx]
                return

        raise ValueError("Provided edge does not exist in graph")

    def removeNode(self, node: Node) -> None:
        """Remove an unconnected node instance."""
        target_index = None
        for idx, current_node in enumerate(self.nodes):
            if current_node is node:
                target_index = idx
                break

        if target_index is None:
            raise ValueError("Provided node does not exist in graph")

        if self._isNodeConnected(node):
            raise ValueError("Cannot remove node because it has connections")

        del self.nodes[target_index]

    def removeNodeByIndex(self, index: Any) -> None:
        """Remove an unconnected node identified by its index."""
        target_node = None

        for node in self.nodes:
            if str(getattr(node, "index", None)) == str(index):
                target_node = node
                break

        if target_node is None:
            raise ValueError("No node found for the provided index")

        if self._isNodeConnected(target_node):
            raise ValueError("Cannot remove node because it has connections")

        for idx, current_node in enumerate(self.nodes):
            if current_node is target_node:
                del self.nodes[idx]
                return

        raise ValueError("No node found for the provided index")

    def _isNodeConnected(self, node):
        node_id = self._getNodeId(node)

        for edge in self.edges:
            edge_node1_id = self._getNodeId(edge.node1)
            edge_node2_id = self._getNodeId(edge.node2)

            if edge_node1_id == node_id or edge_node2_id == node_id:
                return True

        return False
    
    def getConnectedOf(self, node: Node) -> list[Node]:
        """Return nodes reached by outgoing edges from ``node``."""
        node_id = self._getNodeId(node)
        matched_nodes = [
            edge.node2 for edge in self.edges
            if self._getNodeId(edge.node1) == node_id
        ]
        return matched_nodes

    def _validateNodesList(self, nodes):
        if nodes is None:
            return []

        if not isinstance(nodes, list):
            raise TypeError("nodes must be a list of Node objects")

        for node in nodes:
            self._validateNode(node)

        return nodes

    def _validateEdgesList(self, edges):
        if edges is None:
            return []

        if not isinstance(edges, list):
            raise TypeError("edges must be a list of Edge objects")

        for edge in edges:
            self._validateEdge(edge)

        return edges

    def _validateNode(self, node):
        if not isinstance(node, Node):
            raise TypeError("node must be of type Node")

        return node

    def _validateEdge(self, edge):
        if not isinstance(edge, Edge):
            raise TypeError("edge must be of type Edge")

        return edge

    def _getNodeId(self, node):
        if node is None:
            return None
        return str(getattr(node, "index", None))

    def toDict(self) -> dict[str, Any]:
        """Serialize the graph to the canonical API dictionary format."""
        return {
            "nodes": [
                {
                    "index": node.index,
                    "data": node.data,
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "index": edge.index,
                    "node1_index": edge.node1.index if edge.node1 is not None else None,
                    "node2_index": edge.node2.index if edge.node2 is not None else None,
                    "data": edge.data,
                }
                for edge in self.edges
            ],
            "cyclic": self.cyclic,
            "directed": self.directed,
        }

    def __repr__(self):
        return (
            f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"cyclic={self.cyclic}, directed={self.directed})"
        )

    def __str__(self):
        return str(self.toDict())
