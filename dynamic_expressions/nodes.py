from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dynamic_expressions.types import (
        BinaryExpressionOperator,
        UnaryExpressionOperator,
    )


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class Node: ...


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class AnyOfNode(Node):
    expressions: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class AllOfNode(Node):
    expressions: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class UnaryExpressionNode(Node):
    operator: UnaryExpressionOperator
    value: Node


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class BinaryExpressionNode(Node):
    operator: BinaryExpressionOperator
    left: Node
    right: Node


@dataclass(slots=True, frozen=True)
class LiteralNode(Node):
    value: Any

    def __hash__(self) -> int:
        return hash((self.value, type(self.value)))


@dataclass(slots=True, frozen=True, kw_only=True)
class CoalesceNode(Node):
    items: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class CaseNode(Node):
    expression: Node
    value: Node


@dataclass(slots=True, frozen=True, kw_only=True)
class MatchNode(Node):
    cases: tuple[CaseNode, ...]
    default: Node | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class FromContextNode(Node):
    field_name: str
