
from .node import Node
from dataclasses import dataclass

@dataclass
class Edge:

    def __init__(self, node1=None, node2=None, data=None, index=None):
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
    
    def swapDirections(self):
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

    def toString(self):
        return (
            f"Edge(index={self.index}, node1={self.node1}, "
            f"node2={self.node2}, data={self.data})"
        )

    def __str__(self):
        return self.toString()

    def _validateNode(self, node):
        if node is None:
            return None

        if not isinstance(node, Node):
            raise TypeError("Edge node must be of type Node")

        return node
    
    
