from __future__ import annotations

from typing import TYPE_CHECKING

from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    LiteralNode,
    Node,
    UnaryExpressionNode,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dynamic_expressions.types import (
        BinaryExpressionOperator,
        UnaryExpressionOperator,
    )


def _unpack_expressions_of(
    node: Node, *, combiner: type[AnyOfNode | AllOfNode]
) -> tuple[Node, ...]:
    if isinstance(node, combiner):
        return node.expressions
    return (node,)


def _combine_any(left: Node, right: Node) -> Node:
    return AnyOfNode(
        expressions=(
            *_unpack_expressions_of(left, combiner=AnyOfNode),
            *_unpack_expressions_of(right, combiner=AnyOfNode),
        ),
    )


def _combine_all(left: Node, right: Node) -> Node:
    return AllOfNode(
        expressions=(
            *_unpack_expressions_of(left, combiner=AllOfNode),
            *_unpack_expressions_of(right, combiner=AllOfNode),
        ),
    )


class Expression[T]:
    __slots__ = ("_node",)

    def __init__(self, node: Node) -> None:
        self._node = node

    @property
    def node(self) -> Node:
        return self._node

    def __repr__(self) -> str:
        return f"Expression({self._node!r})"

    def __hash__(self) -> int:
        return hash(self._node)

    def __bool__(self) -> bool:
        return True

    def in_(self, container: Iterable[object]) -> Expression[bool]:
        return Expression(
            BinaryExpressionNode(
                operator="in",
                left=self._node,
                right=LiteralNode(value=tuple(container)),
            ),
        )

    def _unary(self, operator: UnaryExpressionOperator) -> UnaryExpressionNode:
        return UnaryExpressionNode(
            operator=operator,
            value=self._node,
        )

    def _binary(
        self,
        operator: BinaryExpressionOperator,
        other: object,
    ) -> BinaryExpressionNode:
        return BinaryExpressionNode(
            operator=operator,
            left=self._node,
            right=node_of(other),
        )

    def __pos__(self) -> Expression[T]:
        return Expression(self._unary("+"))

    def __neg__(self) -> Expression[T]:
        return Expression(self._unary("-"))

    def __invert__(self) -> Expression[T]:
        return Expression(self._unary("~"))

    def __abs__(self) -> Expression[T]:
        return Expression(self._unary("abs"))

    def __eq__(self, other: object) -> Expression[bool]:  # type: ignore[override]
        return Expression(self._binary("=", other))

    def __ne__(self, other: object) -> Expression[bool]:  # type: ignore[override]
        return Expression(self._binary("!=", other))

    def __lt__(self, other: object) -> Expression[bool]:
        return Expression(self._binary("<", other))

    def __le__(self, other: object) -> Expression[bool]:
        return Expression(self._binary("<=", other))

    def __gt__(self, other: object) -> Expression[bool]:
        return Expression(self._binary(">", other))

    def __ge__(self, other: object) -> Expression[bool]:
        return Expression(self._binary(">=", other))

    def __and__(self, other: object) -> Expression[bool]:
        return Expression(_combine_all(self._node, node_of(other)))

    def __rand__(self, other: object) -> Expression[bool]:
        return Expression(_combine_all(node_of(other), self._node))

    def __or__(self, other: object) -> Expression[bool]:
        return Expression(_combine_any(self._node, node_of(other)))

    def __ror__(self, other: object) -> Expression[bool]:
        return Expression(_combine_any(node_of(other), self._node))

    def __add__(self, other: object) -> Expression[T]:
        return Expression(self._binary("+", other))

    def __radd__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) + self.node

    def __sub__(self, other: object) -> Expression[T]:
        return Expression(self._binary("-", other))

    def __rsub__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) - self.node

    def __mul__(self, other: object) -> Expression[T]:
        return Expression(self._binary("*", other))

    def __rmul__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) * self.node

    def __truediv__(self, other: object) -> Expression[T]:
        return Expression(self._binary("/", other))

    def __rtruediv__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) / self.node

    def __floordiv__(self, other: object) -> Expression[int]:
        return Expression(self._binary("//", other))

    def __rfloordiv__(self, other: object) -> Expression[int]:
        return Expression(node_of(other)) // self.node

    def __mod__(self, other: object) -> Expression[T]:
        return Expression(self._binary("%", other))

    def __rmod__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) % self.node

    def __pow__(self, other: object) -> Expression[T]:
        return Expression(self._binary("^", other))

    def __rpow__(self, other: object) -> Expression[T]:
        return Expression(node_of(other)) ** self.node


type AnyExpression[T] = Expression[T] | Node | T


def node_of[T](other: AnyExpression[T]) -> Node:
    if isinstance(other, Expression):
        return other.node
    if isinstance(other, Node):
        return other
    return LiteralNode(value=other)
