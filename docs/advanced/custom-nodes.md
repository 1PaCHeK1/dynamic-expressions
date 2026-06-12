# Custom nodes

Extend the library by defining a new node dataclass and a matching visitor, then registering both in the dispatcher.

## Step 1 — Define the node

Subclass `Node`. Keep it frozen and hashable (the default for `@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)`):

```python
from dataclasses import dataclass

from dynamic_expressions.nodes import Node

@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class UppercaseNode(Node):
    text: Node
```

## Step 2 — Implement the visitor

Subclass `Visitor` and use `dispatch` to evaluate child nodes:

```python
from dynamic_expressions.visitors import Dispatch, Visitor

class UppercaseVisitor(Visitor[UppercaseNode, object]):
    async def visit(
        self,
        *,
        node: UppercaseNode,
        dispatch: Dispatch[object],
        context: object,
    ) -> str:
        value = await dispatch(node.text, context)
        return str(value).upper()
```

## Step 3 — Register in the dispatcher

```python
import asyncio

from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import LiteralNode
from dynamic_expressions.visitors import LiteralVisitor

async def main() -> None:
    dispatcher = VisitorDispatcher(
        visitors={
            LiteralNode: LiteralVisitor(),
            UppercaseNode: UppercaseVisitor(),
        },
    )
    node = UppercaseNode(text=LiteralNode(value="hello"))
    assert await dispatcher.visit(node, None) == "HELLO"

asyncio.run(main())
```

Every node type that can appear in your tree must have a registered visitor. Missing registrations raise `KeyError` at evaluation time.

## Serialization

Built-in [Pydantic](../serialization/pydantic.md) and [AST](../serialization/ast.md) parsers only know about standard nodes. For custom nodes:

- Add a Pydantic schema with `to_node()` and register it in `PydanticExpressionParser(types=...)`.
- Or add an `ExpressionHandler` for the AST parser.

## Optional: DSL integration

To use custom nodes from the context DSL, wrap them in `Expression` manually or add helper functions in your application layer:

```python
from dynamic_expressions.context import AnyExpression, Expression, node_of

def uppercase(expr: AnyExpression[str]) -> Expression[str]:
    return Expression(UppercaseNode(text=node_of(expr)))
```
