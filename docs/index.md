# Dynamic-Expressions

A Python library for building, evaluating, and serializing expression trees. Compose rules as immutable AST nodes, evaluate them asynchronously with a visitor dispatcher, persist them as JSON and parse the ones from python-like code or JSON.

## Features

- **Immutable node trees** — hashable dataclasses suitable for caching and comparison
- **Visitor pattern** — swap evaluation behavior per node type without changing the tree
- **Context DSL** — compose rules with Python operators (`&`, `|`, `==`, `in_`, …)
- **Serialization & Parsing** — Pydantic JSON schemas and AST string parsers
- **Caching** — Redis-backed cache extensions with configurable policies
- **Middlewares** — wrap visitor calls for logging, timing, etc

## Installation

```bash
pip install dynamic-expressions
```

With all optional dependencies:

```bash
pip install dynamic-expressions[cache-redis,serialization-pydantic,serialization-msgspec]
```

## Minimal example

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

## Documentation map

| Section | Description |
|---------|-------------|
| [Getting started](getting-started.md) | Quickstart in five minutes |
| [Concepts](concepts/architecture.md) | Architecture, nodes, visitors, dispatcher, DSL |
| [Extending](extending/custom-nodes.md) | Custom nodes, extensions, middlewares |
| [Serialization](serialization/index.md) | Pydantic, AST, MsgSpec |
| [Cookbook](cookbook/index.md) | End-to-end recipes |

## Next steps

Continue with [Getting started](getting-started.md) or jump to the [Basic cookbook](cookbook/basic.md) for a typed access-control scenario.
