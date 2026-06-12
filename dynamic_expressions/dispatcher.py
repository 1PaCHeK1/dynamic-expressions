import functools
from collections.abc import Mapping, Sequence
from contextlib import AsyncExitStack
from typing import Any

from dynamic_expressions.context.expression import Expression
from dynamic_expressions.extensions import (
    OnVisitExtension,
)
from dynamic_expressions.middlewares import MiddlewareStack, OnVisitMiddleware
from dynamic_expressions.nodes import Node
from dynamic_expressions.types import EmptyContext, ExecutionContext
from dynamic_expressions.visitors import Visitor


class VisitorDispatcher[Context: EmptyContext]:
    """Resolve and evaluate expression nodes with registered visitors.

    The dispatcher selects a visitor by concrete node type, runs optional
    extensions and middlewares, and caches results per node for the duration
    of a single ``visit`` call.

    Example:
        ```python
        dispatcher = VisitorDispatcher(
            visitors={
                LiteralNode: LiteralVisitor(),
                BinaryExpressionNode: BinaryExpressionVisitor(),
            },
        )
        result = await dispatcher.visit(expression_node, context)
        ```

    """

    def __init__(
        self,
        visitors: Mapping[type[Node], Visitor[Any, Any]],
        extensions: Sequence[OnVisitExtension[Context]] = (),
        middlewares: Sequence[OnVisitMiddleware[Context]] = (),
    ) -> None:
        """Configure visitors and optional hooks around node evaluation.

        Args:
            visitors: Mapping from node class to the visitor that evaluates it.
            extensions: Lifecycle hooks entered before each node is visited.
            middlewares: Middleware chain wrapping the selected visitor.

        """
        self._visitors = visitors
        self._on_visit_exts = extensions
        self._middlewares = middlewares

    async def visit(
        self,
        node: Node | Expression[Any],
        context: Context,
    ) -> Any:  # noqa: ANN401
        """Evaluate an expression tree against ``context``.

        Accepts either a [Node][dynamic_expressions.nodes.Node] or an
        [Expression][dynamic_expressions.context.expression.Expression] wrapper.
        Results for individual nodes are memoized for the lifetime of this
        call via an internal ``ExecutionContext``.

        Args:
            node: Root node or expression to evaluate.
            context: Input data passed to visitors and nested dispatches.

        Returns:
            The evaluated result of ``node``.

        """
        if isinstance(node, Expression):
            node = node.node
        execution_context = ExecutionContext()
        return await self._visit(
            node=node,
            context=context,
            execution_context=execution_context,
        )

    async def _visit(
        self,
        node: Node,
        context: Context,
        execution_context: ExecutionContext,
    ) -> Any:  # noqa: ANN401
        async with AsyncExitStack() as stack:
            for ext in self._on_visit_exts:
                await stack.enter_async_context(
                    ext.on_visit(
                        node=node,
                        provided_context=context,
                        execution_context=execution_context,
                    )
                )

            if node in execution_context.cache:
                return execution_context.cache[node]

            visitor = self._visitors[type(node)]
            middleware_stack = MiddlewareStack(
                middlewares=self._middlewares,
                visitor=visitor,
                dispatch=functools.partial(
                    self._visit,
                    execution_context=execution_context,
                ),
            )
            result = await middleware_stack.call(
                node=node,
                context=context,
            )
            execution_context.cache[node] = result
            return result
