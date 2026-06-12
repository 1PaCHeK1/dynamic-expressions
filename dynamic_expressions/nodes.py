from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dynamic_expressions.types import (
        BinaryExpressionOperator,
        UnaryExpressionOperator,
    )


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class Node:
    """Base class for expression AST nodes.

    Subclass this type to define new node kinds. Each node must be hashable
    because the dispatcher caches evaluation results keyed by the node identity.
    """


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class AnyOfNode(Node):
    """Logical OR over a sequence of child expressions.

    Evaluates to a True value if at least one child expression is truthy.
    Pair with [AnyOfVisitor][dynamic_expressions.visitors.AnyOfVisitor].

    Attributes:
        expressions: Child nodes are evaluated in order until one of them is truthy.

    """

    expressions: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class AllOfNode(Node):
    """Logical AND over a sequence of child expressions.

    Evaluates to a True value only when every child expression is truthy.
    Pair with [AllOfVisitor][dynamic_expressions.visitors.AllOfVisitor].

    Attributes:
        expressions: Child nodes are evaluated in order; all must be truthy.

    """

    expressions: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class UnaryExpressionNode(Node):
    """Unary operator applied to a single child expression.

    Pair with [UnaryExpressionVisitor][dynamic_expressions.visitors.UnaryExpressionVisitor].
    Supported operators are listed in ``UnaryExpressionOperator``.

    Attributes:
        operator: Unary operator name, for example ``"not"`` or ``"-"``.
        value: Operand is evaluated before the operator is applied.

    """

    operator: UnaryExpressionOperator
    value: Node


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class BinaryExpressionNode(Node):
    """Binary operator applied to two child expressions.

    Pair with [BinaryExpressionVisitor][dynamic_expressions.visitors.BinaryExpressionVisitor].
    Supported operators are listed in ``BinaryExpressionOperator``.

    Attributes:
        operator: Binary operator name, for example ``"="`` or ``"+"``.
        left: Left-hand operand.
        right: Right-hand operand.

    """

    operator: BinaryExpressionOperator
    left: Node
    right: Node


@dataclass(slots=True, frozen=True)
class LiteralNode(Node):
    """Constant value embedded in an expression tree.

    Pair with [LiteralVisitor][dynamic_expressions.visitors.LiteralVisitor]. When
    ``value`` is a ``tuple``, nested [Node][dynamic_expressions.nodes.Node]
    instances are recursively evaluated during the visitation.

    Attributes:
        value: Constant payload, or a collection that may contain nested nodes.

    """

    value: Any

    def __hash__(self) -> int:
        """Return a hash based on the literal value and its runtime type."""
        return hash((self.value, type(self.value)))


@dataclass(slots=True, frozen=True, kw_only=True)
class CoalesceNode(Node):
    """Return the first truthy child expression.

    Similar to SQL ``COALESCE``. Pair with
    [CoalesceVisitor][dynamic_expressions.visitors.CoalesceVisitor].

    Attributes:
        items: Candidates are evaluated in order; the first truthy result wins.

    """

    items: tuple[Node, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class CaseNode(Node):
    """Single branch inside a [MatchNode][dynamic_expressions.nodes.MatchNode].

    Do not evaluate this node directly. It is handled only as part of
    [MatchNode][dynamic_expressions.nodes.MatchNode] by
    [MatchVisitor][dynamic_expressions.visitors.MatchVisitor].

    Attributes:
        expression: Condition is evaluated to decide whether this branch matches.
        value: Result is returned when the condition is truthy.

    """

    expression: Node
    value: Node


@dataclass(slots=True, frozen=True, kw_only=True)
class MatchNode(Node):
    """Pattern match over ``CaseNode`` branches.

    Returns the value of the first case whose condition is truthy, or the
    optional default branch. Pair with
    [MatchVisitor][dynamic_expressions.visitors.MatchVisitor].

    Attributes:
        cases: Branches are tested in order.
        default: Fallback node is returned if no case matches.

    """

    cases: tuple[CaseNode, ...]
    default: Node | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class FromContextNode(Node):
    """Read a field from the evaluation context.

    The field name may use dot notation (``"user.name"``) to traverse nested
    attributes. Pair with
    [FromContextNodeVisitor][dynamic_expressions.visitors.FromContextNodeVisitor].

    Attributes:
        field_name: Attribute path is resolved from the dispatcher context.

    """

    field_name: str
