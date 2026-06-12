# AST

Store rules as strings in configuration or a database and parse them into node trees at runtime.

## Scenario

Product rules live in plain text. At startup the service parses each rule once and reuses the resulting nodes for every request.

## Parse Python-like expressions

`ExpressionEvalParser` accepts a restricted subset of Python syntax and returns [nodes](../concepts/nodes.md):

```python
from dynamic_expressions.serialization.ast import (
    ExpressionEvalParser,
    FromContextAttributeHandler,
    get_builtin_handlers,
)

parser = ExpressionEvalParser(handlers=[*get_builtin_handlers(), FromContextAttributeHandler()])

node = parser.parse("2 + 2 * 2")
chained_comparison = parser.parse("1 < ctx.grade < 10")
boolean_rule = parser.parse("ctx.score > 50 and ctx.active or ctx.is_admin")
```

Supported constructs include literals, arithmetic, comparisons, chained comparisons, `and` / `or`, and unary operators such as `not` and `-`.

Invalid syntax raises `ExpressionInvalidError`. Unsupported AST nodes raise `UnknownAstNodeError`.

## Read fields from context

Add `FromContextAttributeHandler` to map attribute access to [FromContextNode](../concepts/nodes.md#from-context):

```python
class UserContext(Context):
    is_admin: Mapped[bool]
    division_id: Mapped[int]
    grade_level: Mapped[int]


RULES = {
    "can_manage_projects": (
        "ctx.is_admin or (ctx.division_id in (1, 2, 3) and ctx.grade_level > 3)"
    ),
}


def build_parser() -> ExpressionEvalParser:
    return ExpressionEvalParser(
        handlers=[
            *get_builtin_handlers(), 
            FromContextAttributeHandler(alias="ctx"),
        ],
    )


def build_dispatcher() -> VisitorDispatcher[UserContext]:
    return VisitorDispatcher(
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            FromContextNode: FromContextNodeVisitor(),
            LiteralNode: LiteralVisitor(),
            UnaryExpressionNode: UnaryExpressionVisitor(),
        },
    )


async def main() -> None:
    parser = build_parser()
    dispatcher = build_dispatcher()

    compiled_rules = {name: parser.parse(source) for name, source in RULES.items()}

    user = UserContext(is_admin=False, division_id=2, grade_level=5)
    node = compiled_rules["can_manage_projects"]

    assert await dispatcher.visit(node, user) is True


asyncio.run(main())
```

### Custom context alias

If your templates use `user.` instead of `ctx.`, pass a different alias:

```python
parser = ExpressionEvalParser(
    handlers=[*get_builtin_handlers(), FromContextAttributeHandler(alias="user")],
)

node = parser.parse("user.age > 18")
assert node.field_name == "age"  # type: ignore[attr-defined]
```

Only prefixed attribute names are allowed; bare names such as `is_admin` remain unsupported unless you add a custom handler.
