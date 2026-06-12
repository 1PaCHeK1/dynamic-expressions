# AST serialization

Parse Python-like expression strings into node trees using `ExpressionEvalParser`. The parser walks a restricted Python AST and maps nodes via pluggable handlers.

## ExpressionEvalParser

::: dynamic_expressions.serialization.ast.parser.ExpressionEvalParser

```python
from dynamic_expressions.serialization.ast import (
    ExpressionEvalParser,
    FromContextAttributeHandler,
    get_builtin_handlers,
)

parser = ExpressionEvalParser(
    handlers=[*get_builtin_handlers(), FromContextAttributeHandler()],
)

node = parser.parse("2 + 2 * 2")
chained = parser.parse("1 < ctx.grade < 10")
boolean_rule = parser.parse("ctx.score > 50 and ctx.active or ctx.is_admin")
```

### Supported syntax

Built-in handlers cover:

- Literals (`int`, `str`, `bool`, tuples, lists)
- Arithmetic and comparisons (`+`, `-`, `*`, `/`, `//`, `%`, `^`, `==`, `<`, `in`, …)
- Chained comparisons (`1 < x < 10` → `AllOfNode`)
- Boolean operators (`and` / `or`)
- Unary operators (`not`, `-`, `+`, `~`)

### Errors

| Exception | When |
|-----------|------|
| `ExpressionInvalidError` | Invalid Python syntax |
| `UnknownAstNodeError` | AST node type with no matching handler |

Empty strings return `None`.

## Context field access

`FromContextAttributeHandler` maps prefixed attribute access to [FromContextNode](../concepts/nodes.md#from-context):

```python
parser = ExpressionEvalParser(
    handlers=[*get_builtin_handlers(), FromContextAttributeHandler(alias="ctx")],
)
node = parser.parse("ctx.is_admin")
assert node.field_name == "is_admin"  # type: ignore[attr-defined]
```

Custom alias:

```python
FromContextAttributeHandler(alias="user")  # user.age > 18
```

Bare names (`is_admin`) are not supported unless you add a custom handler.

## Custom handlers

Implement `ExpressionHandler`:

```python
from dynamic_expressions.serialization.ast.handlers import ExpressionHandler

class MyHandler(ExpressionHandler[ast.Call, Node]):
    def satisfy(self, ast_) -> bool:
        return isinstance(ast_, ast.Call) and ...

    def map(self, ast_, dispatch) -> Node:
        ...
```

Add your handler to the parser's `handlers` list. Handlers are tried in order; the first matching `satisfy()` wins.

::: dynamic_expressions.serialization.ast.handlers.ExpressionHandler

Full recipe: [AST cookbook](../cookbook/ast.md).
