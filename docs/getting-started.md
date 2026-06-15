# Getting started

This guide walks through building a node tree, wiring a dispatcher, and evaluating an expression in a few minutes.

## 1. Install

```bash
pip install dynamic-expressions
```

## 2. Build a node tree

Nodes are immutable dataclasses. Construct them directly or use the [context DSL](concepts/context-dsl.md) for operator syntax.

```python
from dynamic_expressions.nodes import BinaryExpressionNode, LiteralNode

expression = BinaryExpressionNode(
    operator="+",
    left=LiteralNode(value=10),
    right=LiteralNode(value=32),
)
```

This tree represents `10 + 32`.

## 3. Create a dispatcher

Register a visitor for every node type that can appear in your tree:

```python
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.types import EmptyContext
from dynamic_expressions.visitors import BinaryExpressionVisitor, LiteralVisitor

dispatcher = VisitorDispatcher[EmptyContext](
    visitors={
        LiteralNode: LiteralVisitor(),
        BinaryExpressionNode: BinaryExpressionVisitor(),
    },
)
```

## 4. Evaluate

`visit` is async. Pass the root node and a context object (use `None` when no context is needed):

```python
import asyncio

async def main() -> None:
    result = await dispatcher.visit(expression, None)
    print(result)  # 42

asyncio.run(main())
```

## 5. Use context for dynamic rules

When expressions read runtime data, define a typed context and use the DSL:

```python
from dynamic_expressions.context import Context, Mapped

class UserContext(Context):
    is_admin: Mapped[bool]

rule = UserContext.is_admin  # builds a FromContextNode
user = UserContext(is_admin=True)
assert asyncio.run(dispatcher.visit(rule, user)) is True
```

Register `FromContextNode: FromContextNodeVisitor()` in the dispatcher. See [Context DSL](concepts/context-dsl.md) and the [Basic cookbook](cookbook/basic.md).

## Where to go next

- [Architecture](concepts/architecture.md) — how evaluation, caching, and hooks fit together
- [Nodes reference](concepts/nodes.md) — all built-in node types and operators
- [Serialization](serialization/index.md) — store rules as JSON or strings
- [Cookbook](cookbook/index.md) — complete application scenarios
