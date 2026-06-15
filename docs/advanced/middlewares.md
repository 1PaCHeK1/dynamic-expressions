# Middlewares

Middlewares wrap individual visitor calls. Unlike [extensions](./extensions/index.md) (async context managers around each node), middlewares form a chain similar to HTTP middleware: each layer receives `call_next` and decides when to invoke the visitor.

::: dynamic_expressions.middlewares.OnVisitMiddleware

## Execution order

For each node (after extensions and per-call cache check):

1. First middleware's `on_visit` is called with `call_next` pointing to the next middleware.
2. The chain continues until all middlewares are exhausted.
3. The innermost call invokes the registered visitor.

```python
import time

from dynamic_expressions.middlewares import OnVisitMiddleware
from dynamic_expressions.nodes import Node
from dynamic_expressions.visitors import Dispatch

class TimingMiddleware[Context](OnVisitMiddleware[Context]):
    async def on_visit(
        self,
        node: Node,
        context: Context,
        call_next: Dispatch[Context],
    ) -> object:
        start = time.perf_counter()
        result = await call_next(node, context)
        elapsed = time.perf_counter() - start
        print(f"{type(node).__name__}: {elapsed:.4f}s")
        return result
```

## Registering middlewares

```python
dispatcher = VisitorDispatcher(
    visitors={...},
    middlewares=[TimingMiddleware()],
)
```

Multiple middlewares run in the registration order — the first-listed is the outermost wrapper.

## Short-circuiting

Middlewares can skip the visitor entirely by not calling `call_next`:

```python
class DenylistMiddleware[Context](OnVisitMiddleware[Context]):
    def __init__(self, blocked: set[type[Node]]) -> None:
        self._blocked = blocked

    async def on_visit(self, node, context, call_next):
        if type(node) in self._blocked:
            raise PermissionError(f"{type(node).__name__} is not allowed")
        return await call_next(node, context)
```

## Extensions vs middlewares

| | Extensions | Middlewares |
|---|-----------|-------------|
| Interface | Async context manager | `on_visit` + `call_next` |
| Typical use | Caching, tracing spans, resource setup | Logging, timing, result transformation |
| Runs when | Before processing by the Visitor and Middlewares | After Extensions and missing cache (`ExecutionContext.cache`), before Visitor |

Both can be combined on the same dispatcher.
