import abc
import operator
import warnings
from collections.abc import Callable, Container, Mapping
from functools import reduce
from typing import Any, ClassVar, Protocol

from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    CaseNode,
    CoalesceNode,
    FromContextNode,
    LiteralNode,
    MatchNode,
    Node,
    UnaryExpressionNode,
)
from dynamic_expressions.types import (
    BinaryExpressionOperator,
    EmptyContext,
    UnaryExpressionOperator,
)


class Dispatch[TContext: EmptyContext](Protocol):
    """Callable that evaluates a child node within the current visit."""

    async def __call__(self, node: Node, context: TContext) -> Any:  # noqa: ANN401
        """Evaluate ``node`` with ``context``.

        Args:
            node: Child node to evaluate.
            context: Context passed through the dispatcher.

        Returns:
            The evaluated result of ``node``.
        """


class Visitor[TNode: Node, TContext: EmptyContext]:
    """Base class for node evaluation strategies.

    Implement ``visit`` for a concrete
    [Node][dynamic_expressions.nodes.Node] subtype and register the visitor in
    [VisitorDispatcher][dynamic_expressions.dispatcher.VisitorDispatcher].

    Example:
        ```python
        dispatcher = VisitorDispatcher(
            visitors={LiteralNode: LiteralVisitor()},
        )
        result = await dispatcher.visit(LiteralNode(value=1), None)
        ```
    """

    @abc.abstractmethod
    async def visit(
        self,
        *,
        node: TNode,
        dispatch: Dispatch[TContext],
        context: TContext,
    ) -> Any:  # noqa: ANN401
        """Evaluate ``node`` using ``dispatch`` for child nodes.

        Args:
            node: Node instance handled by this visitor.
            dispatch: Callback for evaluating nested nodes.
            context: Evaluation context supplied by the dispatcher.

        Returns:
            The computed value for ``node``.
        """
        ...


class AnyOfVisitor(Visitor[AnyOfNode, EmptyContext]):
    """Evaluate [AnyOfNode][dynamic_expressions.nodes.AnyOfNode] as logical OR."""

    async def visit(
        self,
        *,
        node: AnyOfNode,
        dispatch: Dispatch[EmptyContext],
        context: object,
    ) -> bool:
        """Return ``True`` when any child expression is truthy.

        Args:
            node: Node whose ``expressions`` are evaluated in order.
            dispatch: Callback for evaluating each child expression.
            context: Context forwarded to nested dispatches.

        Returns:
            ``True`` if at least one child is truthy, otherwise ``False``.
        """
        for expr in node.expressions:
            value = await dispatch(expr, context)
            if value:
                return True
        return False


class AllOfVisitor(Visitor[AllOfNode, EmptyContext]):
    """Evaluate [AllOfNode][dynamic_expressions.nodes.AllOfNode] as logical AND."""

    async def visit(
        self,
        *,
        node: AllOfNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> bool:
        """Return ``True`` only when every child expression is truthy.

        Args:
            node: Node whose ``expressions`` are evaluated in order.
            dispatch: Callback for evaluating each child expression.
            context: Context forwarded to nested dispatches.

        Returns:
            ``True`` if all children are truthy, otherwise ``False``.
        """
        for expr in node.expressions:
            value = await dispatch(expr, context)
            if not value:
                return False
        return True


class UnaryExpressionVisitor(Visitor[UnaryExpressionNode, EmptyContext]):
    """Evaluate unary operators on a single child expression.

    Attributes:
        operator_mapping: Built-in Python callables keyed by operator name.
    """

    operator_mapping: ClassVar[
        Mapping[UnaryExpressionOperator, Callable[[Any], object]]
    ] = {
        "+": operator.pos,
        "-": operator.neg,
        "~": operator.inv,
        "abs": operator.abs,
        "not": operator.not_,
    }

    async def visit(
        self,
        *,
        node: UnaryExpressionNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> object:
        """Apply ``node.operator`` to the evaluated child value.

        Args:
            node: Unary expression with ``operator`` and ``value``.
            dispatch: Callback used to evaluate ``node.value``.
            context: Context forwarded to nested dispatches.

        Returns:
            The result of the unary operation.

        Raises:
            ValueError: If ``node.operator`` is not registered in
                ``operator_mapping``.
        """
        operator_callable = self.operator_mapping.get(node.operator)
        if operator_callable is None:
            msg = f"Unknown operator '{node.operator}'"
            raise ValueError(msg)

        value = await dispatch(node.value, context)
        return operator_callable(value)


def _visit_getattr(value: Any, properties: Any) -> object:  # noqa: ANN401
    return reduce(getattr, properties.split("."), value)


def _visit_in(left: Any, right: Any) -> bool:  # noqa: ANN401
    if isinstance(left, Container) and not isinstance(right, Container):
        warnings.warn(
            (
                'BinaryExpressionNode(operator="in", left=<container>, right=<search value>) is deprecated, '
                'use BinaryExpressionNode(operator="in", left=<search value>, right=<container>)'
            ),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return operator.contains(left, right)
    return operator.contains(right, left)


class BinaryExpressionVisitor(Visitor[BinaryExpressionNode, EmptyContext]):
    """Evaluate binary operators on two child expressions.

    Attributes:
        operator_mapping: Built-in Python callables keyed by operator name.
    """

    operator_mapping: ClassVar[
        Mapping[BinaryExpressionOperator, Callable[[Any, Any], object]]
    ] = {
        "=": operator.eq,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "!=": operator.ne,
        "in": _visit_in,
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "//": operator.floordiv,
        "%": operator.mod,
        "^": operator.pow,
        "&": operator.and_,
        "|": operator.or_,
        "getitem": operator.getitem,
        "getattr": _visit_getattr,
    }

    async def visit(
        self,
        *,
        node: BinaryExpressionNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> object:
        """Apply ``node.operator`` to the evaluated left and right operands.

        Args:
            node: Binary expression with ``operator``, ``left``, and ``right``.
            dispatch: Callback used to evaluate both operands.
            context: Context forwarded to nested dispatches.

        Returns:
            The result of the binary operation.

        Raises:
            ValueError: If ``node.operator`` is not registered in
                ``operator_mapping``.
        """
        operator_callable = self.operator_mapping.get(node.operator)
        if operator_callable is None:
            msg = f"Unknown operator '{node.operator}'"
            raise ValueError(msg)
        left = await dispatch(node.left, context)
        right = await dispatch(node.right, context)
        return operator_callable(left, right)


class LiteralVisitor(Visitor[LiteralNode, EmptyContext]):
    """Evaluate [LiteralNode][dynamic_expressions.nodes.LiteralNode] constants."""

    async def visit(
        self,
        *,
        node: LiteralNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> Any:  # noqa: ANN401
        """Return the literal value, evaluating nested nodes in collections.

        When ``node.value`` is a ``tuple`` or ``list``, any nested
        [Node][dynamic_expressions.nodes.Node] items are dispatched and
        replaced with their results.

        Args:
            node: Literal node whose ``value`` is returned or expanded.
            dispatch: Callback for nested nodes inside collections.
            context: Context forwarded to nested dispatches.

        Returns:
            The literal value, or a tuple with nested nodes resolved.
        """
        if isinstance(node.value, (tuple, list)):
            return tuple(
                [
                    await dispatch(item, context) if isinstance(item, Node) else item
                    for item in node.value
                ]
            )
        return node.value


class CoalesceVisitor(Visitor[CoalesceNode, EmptyContext]):
    """Evaluate [CoalesceNode][dynamic_expressions.nodes.CoalesceNode] branches."""

    async def visit(
        self,
        *,
        node: CoalesceNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> Any:  # noqa: ANN401
        """Return the first truthy child result.

        Args:
            node: Coalesce node whose ``items`` are tried in order.
            dispatch: Callback for evaluating each candidate.
            context: Context forwarded to nested dispatches.

        Returns:
            The first truthy result, or ``None`` when every item is falsy.
        """
        for item in node.items:
            node_result = await dispatch(item, context)
            if node_result:
                return node_result
        return None


class CaseVisitor(Visitor[CaseNode, EmptyContext]):
    """Guard visitor that rejects direct [CaseNode][dynamic_expressions.nodes.CaseNode] evaluation."""

    async def visit(
        self,
        *,
        node: CaseNode,  # noqa: ARG002
        dispatch: Dispatch[EmptyContext],  # noqa: ARG002
        context: EmptyContext,  # noqa: ARG002
    ) -> Any:  # noqa: ANN401
        """Raise an error because [CaseNode][dynamic_expressions.nodes.CaseNode] must live inside [MatchNode][dynamic_expressions.nodes.MatchNode].

        Args:
            node: Case node that was dispatched directly.
            dispatch: Unused.
            context: Unused.

        Raises:
            ValueError: Always, to signal incorrect node usage.
        """
        msg = "Use CaseNode only in MatchNode"
        raise ValueError(msg)


class MatchVisitor(Visitor[MatchNode, EmptyContext]):
    """Evaluate [MatchNode][dynamic_expressions.nodes.MatchNode] pattern matching."""

    async def visit(
        self,
        *,
        node: MatchNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> Any:  # noqa: ANN401
        """Return the value of the first matching case.

        Each [CaseNode][dynamic_expressions.nodes.CaseNode] condition is evaluated
        in order. When a condition is truthy, its ``value`` child is returned.
        If no case matches, ``node.default`` is evaluated when present.

        Args:
            node: Match node with ``cases`` and optional ``default``.
            dispatch: Callback for case conditions and result nodes.
            context: Context forwarded to nested dispatches.

        Returns:
            The evaluated value of the first matching case or the default.

        Raises:
            ValueError: When no case matches and ``default`` is ``None``.
        """
        for case_ in node.cases:
            if await dispatch(case_.expression, context):
                return await dispatch(case_.value, context)
        if node.default is not None:
            return await dispatch(node.default, context)

        msg = "MatchCase doesn't find CaseNode with the appropriate expression"
        raise ValueError(msg)


class FromContextNodeVisitor[TContext](Visitor[FromContextNode, TContext]):
    """Resolve [FromContextNode][dynamic_expressions.nodes.FromContextNode] from context."""

    async def visit(
        self,
        *,
        node: FromContextNode,
        dispatch: Dispatch[TContext],  # noqa: ARG002
        context: TContext,
    ) -> Any:  # noqa: ANN401
        """Read ``node.field_name`` from ``context``.

        Dot-separated segments in ``field_name`` are resolved with chained
        attribute access, for example ``"user.profile.name"``.

        Args:
            node: Context lookup node with ``field_name``.
            dispatch: Unused.
            context: Object whose attributes are read.

        Returns:
            The resolved attribute value.

        Raises:
            AttributeError: When the field path cannot be resolved on
                ``context``.
        """
        try:
            return _visit_getattr(context, node.field_name)
        except AttributeError as e:
            msg = f"Field '{node.field_name}' not found in context of type '{context.__class__.__qualname__}'"
            raise AttributeError(msg) from e
