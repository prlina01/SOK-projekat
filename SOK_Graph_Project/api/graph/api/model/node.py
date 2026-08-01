
from dataclasses import dataclass
from typing import Any

@dataclass
class Node:
    """A graph vertex identified by ``index`` with arbitrary typed attributes."""

    def __init__(self, data: dict[str, Any] | None = None, index: Any = None):
        self.data = data
        self.index = index
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = self._normalizeData(value)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    def addData(self, key: str, value: Any) -> None:
        """Add or replace a node attribute."""
        self.data[key] = value

    def removeData(self, key: str) -> None:
        """Remove an existing node attribute."""
        if key not in self.data:
            raise KeyError(f"Key '{key}' does not exist in node data")
        del self.data[key]

    def toString(self) -> str:
        """Return a readable representation kept for API compatibility."""
        return f"Node(data={self.data}, index={self.index})"

    def __str__(self) -> str:
        return self.toString()

    def _normalizeData(self, data: dict[str, Any] | None) -> dict[str, Any]:
        if data is None:
            return {}
        try:
            return dict(data)
        except Exception as exc:
            raise ValueError("Node data must be a dictionary or dictionary-compatible value") from exc
