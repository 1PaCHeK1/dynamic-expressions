# Pydantic

Persist expression trees as JSON, validate them on input, and rebuild nodes for evaluation.

Install the optional dependency first:

```bash
pip install dynamic-expressions[serialization-pydantic]
```

## Scenario

An HTTP API accepts rule definitions from clients. Pydantic validates the payload, converts it to nodes, and the dispatcher executes the rule.

## Validate JSON from a client

```python
import asyncio
import json

from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    LiteralNode,
)
from dynamic_expressions.serialization.pydantic import (
    BUILTIN_SCHEMAS,
    PydanticExpressionParser,
)
from dynamic_expressions.types import EmptyContext
from dynamic_expressions.visitors import (
    AllOfVisitor,
    AnyOfVisitor,
    BinaryExpressionVisitor,
    LiteralVisitor,
)

RULE_JSON = """
{
  "type": "all-of",
  "expressions": [
    {
      "type": "binary",
      "operator": ">",
      "left": { "type": "literal", "value": 10 },
      "right": { "type": "literal", "value": 0 }
    },
    {
      "type": "any-of",
      "expressions": [
        { "type": "literal", "value": true },
        { "type": "literal", "value": false }
      ]
    }
  ]
}
"""


def build_parser() -> PydanticExpressionParser:
    return PydanticExpressionParser(types=BUILTIN_SCHEMAS)


def build_dispatcher() -> VisitorDispatcher[EmptyContext]:
    return VisitorDispatcher(
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            LiteralNode: LiteralVisitor(),
        },
    )


async def main() -> None:
    parser = build_parser()
    dispatcher = build_dispatcher()

    schema = parser.type_adapter.validate_json(RULE_JSON)
    node = schema.to_node()

    assert await dispatcher.visit(node, None) is True
```

## Serialize back to JSON

Round-trip a rule for storage or logging:

```python
from typing import Any

from dynamic_expressions.serialization.pydantic import (
    AllOfNodeSchema,
    AnyOfNodeSchema,
    BinaryExpressionNodeSchema,
    LiteralNodeSchema,
)

schema = AllOfNodeSchema[Any](
    type="all-of",
    expressions=(
        BinaryExpressionNodeSchema(
            type="binary",
            operator="-",
            left=LiteralNodeSchema(type="literal", value=10),
            right=LiteralNodeSchema(type="literal", value=3),
        ),
        LiteralNodeSchema(type="literal", value=True),
    ),
)

payload = parser.type_adapter.dump_python(schema, mode="json", warnings="none")
stored = json.dumps(payload, indent=2)

restored = parser.type_adapter.validate_json(stored).to_node()
assert await dispatcher.visit(restored, None) is True
```

## From-context and unary nodes

The built-in schemas cover every standard node type:

```python
from dynamic_expressions.serialization.pydantic import (
    FromContextNodeSchema,
    UnaryExpressionNodeSchema,
)

profile_field = FromContextNodeSchema(type="from-context", field_name="user.name")
negated = UnaryExpressionNodeSchema(
    type="unary",
    operator="-",
    value=LiteralNodeSchema(type="literal", value=1),
)

assert profile_field.to_node().field_name == "user.name"
assert negated.to_node().operator == "-"
```

Each schema exposes `.to_node()` so the same validated object can be evaluated immediately or saved for later.
