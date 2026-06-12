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
    def __init__(
        self,
        visitors: Mapping[type[Node], Visitor[Any, Any]],
        extensions: Sequence[OnVisitExtension[Context]] = (),
        middlewares: Sequence[OnVisitMiddleware[Context]] = (),
    ) -> None:
        self._visitors = visitors
        self._on_visit_exts = extensions
        self._middlewares = middlewares

    async def visit(
        self,
        node: Node | Expression[Any],
        context: Context,
    ) -> Any:  # noqa: ANN401
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
