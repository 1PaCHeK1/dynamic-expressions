# Dispatcher

`VisitorDispatcher` is the entry point for evaluating expression trees. It selects a visitor by concrete node type, runs optional extensions and middlewares, and memoizes results per node for the duration of a single `visit` call.

::: dynamic_expressions.dispatcher.VisitorDispatcher
    options:
      members:
        - __init__
        - visit

## Configuration

The dispatcher accepts three optional hook layers:

| Parameter | Type | Purpose |
|-----------|------|---------|
| `visitors` | `Mapping[type[Node], Visitor]` | Required — maps each node class to its evaluator |
| `extensions` | `Sequence[OnVisitExtension]` | Async context managers entered before each node visit |
| `middlewares` | `Sequence[OnVisitMiddleware]` | Middleware chain wrapping the selected visitor |

```python
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import LiteralNode, BinaryExpressionNode
from dynamic_expressions.visitors import LiteralVisitor, BinaryExpressionVisitor
from dynamic_expressions.types import EmptyContext

dispatcher = VisitorDispatcher[EmptyContext](
    visitors={
        LiteralNode: LiteralVisitor(),
        BinaryExpressionNode: BinaryExpressionVisitor(),
    },
)

node = BinaryExpressionNode(
    operator="+",
    left=LiteralNode(value=1),
    right=LiteralNode(value=2),
)
result = await dispatcher.visit(node, None)  # 3
```

`visit` accepts either a `Node` or an [Expression](context-dsl.md) wrapper.

## Execution flow

1. Extensions run first (for example, [Redis cache lookup](../extending/extensions.md)).
2. If the node is already in `ExecutionContext.cache`, the cached value is returned.
3. Middlewares wrap the visitor call.
4. The visitor evaluates the node, using `dispatch` for children.
5. The result is stored in `ExecutionContext.cache` for the rest of this `visit` call.

::: dynamic_expressions.types.ExecutionContext

Per-call memoization means the same node instance evaluated twice within one `visit` is computed only once. This is separate from Redis caching via extensions.

## Related topics

- [Architecture](architecture.md) — full evaluation pipeline
- [Extensions](../extending/extensions.md) — cross-cutting hooks (caching, metrics)
- [Middlewares](../extending/middlewares.md) — wrap individual visitor calls
