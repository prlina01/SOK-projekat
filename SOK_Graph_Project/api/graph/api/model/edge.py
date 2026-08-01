
from .node import Node
from dataclasses import dataclass
from typing import Any

@dataclass
class Edge:
    """A graph relationship with endpoints, an identifier, and typed attributes."""

    def __init__(
        self,
        node1: Node | None = None,
        node2: Node | None = None,
        data: dict[str, Any] | None = None,
        index: Any = None,
    ):
        self.node1 = node1
        self.node2 = node2
        self.data = data
        self.index = index

    @property
    def node1(self):
        return self._node1

    @node1.setter
    def node1(self, value):
        self._node1 = self._validateNode(value)

    @property
    def node2(self):
        return self._node2

    @node2.setter
    def node2(self, value):
        self._node2 = self._validateNode(value)
    
    def swapDirections(self) -> None:
        """Reverse the relationship direction in place."""
        node3=self.node1
        self.node1=self.node2
        self.node2=node3

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if value is None:
            self._data = {}
            return
        if not isinstance(value, dict):
            raise ValueError("Edge data must be a dictionary")
        self._data = value

    def toString(self) -> str:
        """Return a readable representation kept for API compatibility."""
        return (
            f"Edge(index={self.index}, node1={self.node1}, "
            f"node2={self.node2}, data={self.data})"
        )

    def __str__(self) -> str:
        return self.toString()

    def _validateNode(self, node: Node | None) -> Node | None:
        if node is None:
            return None

        if not isinstance(node, Node):
            raise TypeError("Edge node must be of type Node")

        return node
    
    
