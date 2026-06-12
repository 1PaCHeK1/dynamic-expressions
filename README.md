# Dynamic-Expressions

A Python library for building, evaluating, and serializing expression trees.

[Documentation](https://1pachek1.github.io/dynamic-expressions/)

## Installation

```bash
pip install dynamic-expressions
```

With optional dependencies:

```bash
pip install dynamic-expressions[cache-redis,serialization-pydantic,serialization-msgspec]
```

## Quick example

```python
import asyncio

from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import BinaryExpressionNode, LiteralNode
from dynamic_expressions.types import EmptyContext
from dynamic_expressions.visitors import BinaryExpressionVisitor, LiteralVisitor

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

async def main() -> None:
    result = await dispatcher.visit(node, None)
    assert result == 3

asyncio.run(main())
```

See the [getting started guide](https://1pachek1.github.io/dynamic-expressions/getting-started/) for more.
