# Nodes

A **node** is an immutable, hashable dataclass that stores expression structure. Nodes are not evaluated directly — pass them to a [VisitorDispatcher](dispatcher.md) with matching visitors.

::: dynamic_expressions.nodes.Node
    options:
      members: false


## Literal

::: dynamic_expressions.nodes.LiteralNode
    options:
      members: false


## Any Of

::: dynamic_expressions.nodes.AnyOfNode
    options:
      members: false


## All Of

::: dynamic_expressions.nodes.AllOfNode
    options:
      members: false


## Unary Expression

::: dynamic_expressions.nodes.UnaryExpressionNode
    options:
      members: false

Supported operators:

| Operator | Meaning |
|----------|---------|
| `+` | Unary plus (`operator.pos`) |
| `-` | Negation |
| `~` | Bitwise invert |
| `abs` | Absolute value |
| `not` | Logical not |


## Binary Expression

::: dynamic_expressions.nodes.BinaryExpressionNode
    options:
      members: false

Supported operators:

| Operator | Meaning |
|----------|---------|
| `=` | Equality |
| `!=` | Inequality |
| `<`, `<=`, `>`, `>=` | Comparison |
| `in` | Membership test (`left in right`) |
| `+`, `-`, `*`, `/`, `//`, `%`, `^` | Arithmetic |
| `&`, `\|` | Bitwise and / or |
| `getitem` | Subscript access |
| `getattr` | Dot-separated attribute path |

!!! warning "Operand order for `in`"
    Passing the container as `left` and the search value as `right` still works but emits a `DeprecationWarning`. Prefer `left=<search value>`, `right=<container>`.


## Coalesce

::: dynamic_expressions.nodes.CoalesceNode
    options:
      members: false


## Match

::: dynamic_expressions.nodes.MatchNode
    options:
      members: false


## Case

::: dynamic_expressions.nodes.CaseNode
    options:
      members: false


## From Context

::: dynamic_expressions.nodes.FromContextNode
    options:
      members: false
