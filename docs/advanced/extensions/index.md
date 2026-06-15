# Extensions

Extensions hook into the dispatcher lifecycle via async context managers. Each extension runs **before** a node is visited and can read or populate the per-call `ExecutionContext`.

## OnVisitExtension

::: dynamic_expressions.extensions.OnVisitExtension

```python
import contextlib
from collections.abc import AsyncIterator

from dynamic_expressions.extensions import OnVisitExtension
from dynamic_expressions.nodes import Node
from dynamic_expressions.types import ExecutionContext

class LoggingExtension[Context](OnVisitExtension[Context]):
    @contextlib.asynccontextmanager
    async def on_visit(
        self,
        *,
        node: Node,
        provided_context: Context,
        execution_context: ExecutionContext,
    ) -> AsyncIterator[None]:
        print(f"visiting {type(node).__name__}")
        yield

dispatcher = VisitorDispatcher(
    visitors={...},
    extensions=[LoggingExtension()],
)
```

Pass extensions to `VisitorDispatcher(extensions=[...])`. They are run in order for each node in the tree.
