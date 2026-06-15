# Basic

Use the context DSL when rules are built in Python and evaluated against a typed dataclass.

## Scenario

An internal admin panel grants access when a user is an administrator **or** belongs to an allowed division with sufficient seniority.

## Define context and dispatcher

```python
class UserContext(Context):
    is_admin: Mapped[bool]
    division_id: Mapped[int]
    grade_level: Mapped[int]


def build_dispatcher() -> VisitorDispatcher[UserContext]:
    return VisitorDispatcher(
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            CoalesceNode: CoalesceVisitor(),
            CaseNode: CaseVisitor(),
            FromContextNode: FromContextNodeVisitor(),
            LiteralNode: LiteralVisitor(),
            MatchNode: MatchVisitor(),
            UnaryExpressionNode: UnaryExpressionVisitor(),
        },
    )
```

`Context` fields such as `UserContext.is_admin` become [FromContextNode](../concepts/nodes.md#from-context) expressions automatically.

## Compose a rule

```python
can_manage_projects = UserContext.is_admin | (
    UserContext.division_id.in_((1, 2, 3)) & (UserContext.grade_level > 3)
)

is_guest = not_(UserContext.is_admin)
```

The expression is read by Python, but an immutable node is built internally:

```python
assert isinstance(can_manage_projects.node, AnyOfNode)
```

## Evaluate against runtime data

```python
async def main() -> None:
    dispatcher = build_dispatcher()

    senior_manager = UserContext(is_admin=False, division_id=2, grade_level=5)
    outsider = UserContext(is_admin=False, division_id=99, grade_level=5)

    assert await dispatcher.visit(can_manage_projects, senior_manager) is True
    assert await dispatcher.visit(can_manage_projects, outsider) is False
    assert await dispatcher.visit(is_guest, senior_manager) is True


asyncio.run(main())
```

## Helper operators

For rules that are awkward to express with `&` and `|`, use helpers from `dynamic_expressions.context.operators`:

```python
from dynamic_expressions.context.expression import Expression

active_status = Expression(LiteralNode(value="active"))
fallback_label = coalesce(active_status, "unknown")

discount_label = match(
    [(UserContext.is_admin, "Admin discount")],
    default="Standard price",
)
```

Convert any result back to a node with `expression.node` when you need to pass it to the dispatcher or serialize it later.
