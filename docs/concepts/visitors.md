# Visitors

A **visitor** defines how a concrete node type is evaluated. Register visitors in a [VisitorDispatcher](dispatcher.md) mapping from the node class to the visitor instance.

Each visitor receives:

- `node` — the node being evaluated
- `dispatch` — callback to evaluate child nodes
- `context` — runtime input data passed to the dispatcher

::: dynamic_expressions.visitors.Visitor
    options:
      members:
        - visit

::: dynamic_expressions.visitors.Dispatch

## Built-in visitors

| Visitor | Node | Behavior |
|---------|------|----------|
| `LiteralVisitor` | `LiteralNode` | Returns the constant; resolves nested nodes in collections |
| `AnyOfVisitor` | `AnyOfNode` | Logical OR — returns True if at least one child is truthy |
| `AllOfVisitor` | `AllOfNode` | Logical AND — returns True if all children are truthy |
| `UnaryExpressionVisitor` | `UnaryExpressionNode` | Applies unary operator |
| `BinaryExpressionVisitor` | `BinaryExpressionNode` | Applies binary operator |
| `CoalesceVisitor` | `CoalesceNode` | First truthy child, or `None` |
| `MatchVisitor` | `MatchNode` | First matching case value, or default |
| `CaseVisitor` | `CaseNode` | Raises `ValueError` — must live inside `MatchNode` |
| `FromContextNodeVisitor` | `FromContextNode` | Reads `field_name` from context |

### Literal

::: dynamic_expressions.visitors.LiteralVisitor
    options:
      members: false

### Any Of

::: dynamic_expressions.visitors.AnyOfVisitor
    options:
      members: false

### All Of

::: dynamic_expressions.visitors.AllOfVisitor
    options:
      members: false

### Unary Expression

::: dynamic_expressions.visitors.UnaryExpressionVisitor
    options:
      members: false

### Binary Expression

::: dynamic_expressions.visitors.BinaryExpressionVisitor
    options:
      members: false

### Coalesce

::: dynamic_expressions.visitors.CoalesceVisitor
    options:
      members: false

### Match

::: dynamic_expressions.visitors.MatchVisitor
    options:
      members: false

### Case

::: dynamic_expressions.visitors.CaseVisitor
    options:
      members: false

### From Context

::: dynamic_expressions.visitors.FromContextNodeVisitor
    options:
      members: false

## Overriding behavior

Subclass a built-in visitor and override `visit`, or replace `operator_mapping` on unary/binary visitors. Register the subclass in the dispatcher:

```python
class StrictBinaryVisitor(BinaryExpressionVisitor):
    async def visit(self, *, node, dispatch, context):
        result = await super().visit(node=node, dispatch=dispatch, context=context)
        if result is None:
            raise ValueError("Null results are not allowed")
        return result

dispatcher = VisitorDispatcher(
    visitors={
        BinaryExpressionNode: StrictBinaryVisitor(),
        # ... other visitors
    },
)
```

See [Custom nodes](../advanced/custom-nodes.md) for adding entirely new node types.
