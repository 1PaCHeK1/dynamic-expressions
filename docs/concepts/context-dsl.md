# Context DSL

The context DSL allows you to compose expression trees using Python syntax. Subclass `Context` with `Mapped` fields — accessing the class field returns an `Expression` that builds a [FromContextNode](nodes.md#from-context) automatically.

::: dynamic_expressions.context.model.Context

## Defining a context

```python
from dynamic_expressions.context import Context, Mapped

class UserContext(Context):
    is_admin: Mapped[bool]
    division_id: Mapped[int]
    grade_level: Mapped[int]

# Class access builds expressions; instance access returns field values
user = UserContext(is_admin=True, division_id=1, grade_level=5)
assert user.is_admin is True
assert UserContext.is_admin.node.field_name == "is_admin"
```

Use `mapped_field` for defaults, same as `dataclasses.field`:

```python
from dynamic_expressions.context import mapped_field

class Settings(Context):
    threshold: Mapped[int] = mapped_field(default=10)
```

## Expression operators

::: dynamic_expressions.context.expression.Expression
    options:
      members: false

`Expression` overloads Python operators to build node trees without calling constructors directly:

| Syntax | Node |
|--------|------|
| `a & b` | `AllOfNode` (AND) |
| `a | b` | `AnyOfNode` (OR) |
| `a == b`, `a != b`, `<`, `<=`, `>`, `>=` | `BinaryExpressionNode` |
| `a + b`, `-`, `*`, `/`, `//`, `%`, `**` | `BinaryExpressionNode` |
| `~a`, `-a`, `+a`, `abs(a)` | `UnaryExpressionNode` |
| `a.in_(container)` | `BinaryExpressionNode(operator="in", ...)` |

```python
rule = UserContext.is_admin | (
    UserContext.division_id.in_((1, 2, 3)) & (UserContext.grade_level > 3)
)
assert rule.node  # AnyOfNode — ready for dispatcher.visit()
```

Literals and raw nodes are coerced automatically via `node_of`:

```python
from dynamic_expressions.context import node_of

node = node_of(42)           # LiteralNode(value=42)
node = node_of(some_expr)    # unwraps Expression
```

## Helper functions

For constructs that are awkward with operators, use helpers from `dynamic_expressions.context.operators`:

```python
from dynamic_expressions.context.operators import not_, and_, or_, coalesce, match
from dynamic_expressions.nodes import LiteralNode

is_guest = not_(UserContext.is_admin)

combined = and_(UserContext.is_admin, UserContext.grade_level > 3)

either = or_(UserContext.is_admin, UserContext.grade_level > 5)

label = coalesce(
    UserContext.role,
    LiteralNode(value="guest"),
)

tier = match(
    [(UserContext.is_admin, LiteralNode(value="admin"))],
    default=LiteralNode(value="guest"),
)
```

`match` also accepts a mapping or a `value=` argument for equality-style matching.

## Evaluation

Pass `expression.node` (or the expression itself) to the dispatcher:

```python
result = await dispatcher.visit(rule, user)
```

See the [Basic cookbook](../cookbook/basic.md) for a complete access-control example.
