# AST + Context

Combine rules loaded from external storage with static checks written in the [context DSL](../concepts/context-dsl.md).

## Scenario

An access-control service stores tenant-specific rules in the database as plain strings (`"ctx.age >= 18"`). Operators can edit them without redeploying the app. Some checks stay hardcoded in code — for example, administrators always get access regardless of other rules.

At startup (or on cache invalidation) the service parses DB rules once, merges them with static expressions, and evaluates the combined tree on every request.

## Define context

```python
from dynamic_expressions.context import Context, Expression, Mapped

class UserContext(Context):
    age: Mapped[int]
    is_admin: Mapped[bool]
```

Fields accessed as `UserContext.is_admin` become [FromContextNode](../concepts/nodes.md#from-context) nodes.

## Load a rule from the database

```python
from dynamic_expressions.serialization.ast import (
    ExpressionEvalParser,
    FromContextAttributeHandler,
    get_builtin_handlers,
)

parser = ExpressionEvalParser(
    handlers=[
        *get_builtin_handlers(),
        FromContextAttributeHandler(),
    ],
)

# Simulates a row from the database
RULES_FROM_DB = {
    "allow_adult": "ctx.age >= 18",
}

rule_from_db = parser.parse(RULES_FROM_DB["allow_adult"])
```

Parse each rule once and reuse the resulting node. Invalid syntax raises `ExpressionInvalidError` — validate when saving to the database or during startup.

## Mix with a static rule

Wrap the parsed node in `Expression` and combine it with DSL operators:

```python
static_rule = UserContext.is_admin
final_rule = Expression(rule_from_db) | static_rule
```

`final_rule` is equivalent to “age is at least 18 **or** user is an admin”. The tree is a single `AnyOfNode` that the dispatcher evaluates in one pass.

!!! tip "Why mix both styles?"
    - **Database strings** — rules that change often or differ per tenant.
    - **Static DSL** — invariants owned by the engineering team (admin bypass, feature flags, emergency kill switches).
    - **`Expression(parsed_node)`** — bridges AST output into the same `&` / `|` API as `UserContext.is_admin`.

## Evaluate

Register all node types that can appear in any of the branches, including nodes produced by the parser:

```python
import asyncio

from dynamic_expressions import nodes, visitors
from dynamic_expressions.dispatcher import VisitorDispatcher

async def main() -> None:
    dispatcher = VisitorDispatcher[UserContext](
        visitors={
            nodes.AllOfNode: visitors.AllOfVisitor(),
            nodes.AnyOfNode: visitors.AnyOfVisitor(),
            nodes.UnaryExpressionNode: visitors.UnaryExpressionVisitor(),
            nodes.BinaryExpressionNode: visitors.BinaryExpressionVisitor(),
            nodes.LiteralNode: visitors.LiteralVisitor(),
            nodes.CoalesceNode: visitors.CoalesceVisitor(),
            nodes.CaseNode: visitors.CaseVisitor(),
            nodes.MatchNode: visitors.MatchVisitor(),
            nodes.FromContextNode: visitors.FromContextNodeVisitor(),
        },
    )

    rule_from_db = parser.parse("ctx.age >= 18")
    static_rule = UserContext.is_admin
    final_rule = Expression(rule_from_db) | static_rule

    for ctx in [
        UserContext(age=20, is_admin=False),  # too young, not admin → True
        UserContext(age=10, is_admin=False),  # too young, not admin → False
        UserContext(age=2, is_admin=True),    # admin bypass → True
    ]:
        result = await dispatcher.visit(final_rule, ctx)
        print(ctx, result)


asyncio.run(main())
```

Output:

```
True
False
True
```


## Related recipes

- [AST](ast.md) — parser handlers, custom `ctx` alias, supported syntax
- [Basic](basic.md) — composing rules entirely in the context DSL
- [Pydantic](pydantic.md) — when rules are stored as JSON instead of strings
