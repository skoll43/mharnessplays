from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Edge:
    target: str
    confidence: float = 0.5
    failures: int = 0


@dataclass
class Cartographer:
    nodes: dict[str, list[Edge]] = field(default_factory=dict)

    def add_node(self, node: str) -> None:
        self.nodes.setdefault(node, [])

    def add_edge(self, source: str, target: str, confidence: float = 0.5) -> None:
        self.add_node(source)
        self.add_node(target)
        self.nodes[source].append(Edge(target=target, confidence=confidence))
