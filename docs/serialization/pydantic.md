# Pydantic serialization

The `dynamic_expressions.serialization.pydantic` module covers two related tasks:

| Component | Purpose |
|-----------|---------|
| [PydanticExpressionParser](#expression-trees) | Parse and validate expression trees as JSON |
| [PydanticSerializer](#pydanticserializer) | Serialize arbitrary Pydantic-validated values to bytes |

Install the optional dependency:

```bash
pip install dynamic-expressions[serialization-pydantic]
```

## Expression trees

Expression JSON is modeled with Pydantic schemas. Each schema exposes `.to_node()` to rebuild runtime [nodes](../concepts/nodes.md).

### Schemas

`BUILTIN_SCHEMAS` covers all standard node types:

- `LiteralNodeSchema` 
- `UnaryExpressionNodeSchema`
- `BinaryExpressionNodeSchema`
- `AnyOfNodeSchema`
- `AllOfNodeSchema`
- `CoalesceNodeSchema`
- `MatchNodeSchema`
- `CaseNodeSchema`
- `FromContextNodeSchema`

Each schema has a discriminated `type` field (for example `"literal"`, `"binary"`, `"all-of"`).

### PydanticExpressionParser

Builds a Pydantic `TypeAdapter` over a union of registered schemas. Use `type_adapter.validate_json()` to parse incoming JSON and `.to_node()` on the result.

::: dynamic_expressions.serialization.pydantic.PydanticExpressionParser

### Validate JSON from a client

```python
import asyncio
import json

from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import AllOfNode, AnyOfNode, BinaryExpressionNode, LiteralNode
from dynamic_expressions.serialization.pydantic import BUILTIN_SCHEMAS, PydanticExpressionParser
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
    { "type": "literal", "value": true }
  ]
}
"""

parser = PydanticExpressionParser(types=BUILTIN_SCHEMAS)
dispatcher = VisitorDispatcher(
    visitors={
        AllOfNode: AllOfVisitor(),
        AnyOfNode: AnyOfVisitor(),
        BinaryExpressionNode: BinaryExpressionVisitor(),
        LiteralNode: LiteralVisitor(),
    },
)

schema = parser.type_adapter.validate_json(RULE_JSON)
node = schema.to_node()
assert asyncio.run(dispatcher.visit(node, None)) is True
```

### Round-trip to JSON

```python
from dynamic_expressions.serialization.pydantic import (
    AllOfNodeSchema,
    BinaryExpressionNodeSchema,
    LiteralNodeSchema,
)

schema = AllOfNodeSchema(
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
```

### Custom node schemas

Register additional schemas when extending the library:

```python
parser = PydanticExpressionParser(types=[*BUILTIN_SCHEMAS, MyCustomNodeSchema])
```

See [Custom nodes](../advanced/custom-nodes.md).

## PydanticSerializer

`PydanticSerializer` implements the [Serializer](index.md#serializer-protocol) protocol for any type that Pydantic can validate — a `BaseModel`, a union, or another supported annotation.

It wraps Pydantic's `TypeAdapter`:

- `serialize` calls `dump_json(..., by_alias=True)`
- `deserialize` calls `validate_json(..., strict=True)`

::: dynamic_expressions.serialization.pydantic.PydanticSerializer

### Serialize a model or union

```python
from pydantic import BaseModel

from dynamic_expressions.serialization.pydantic import PydanticSerializer

class SomeModel(BaseModel):
    id: int

serializer = PydanticSerializer[SomeModel | list[SomeModel]](
    instance_of=SomeModel | list[SomeModel],
)

instance = SomeModel(id=1)
payload = serializer.serialize(instance)
assert serializer.deserialize(payload) == instance
```

### Use with cache policies

When cached evaluation results are Pydantic models rather than plain scalars, pass a `PydanticSerializer` as the per-policy `serializer` on [CachePolicy](../advanced/extensions/cache.md):

```python
policy = CachePolicy[MyContext](
    types=(CoalesceNode,),
    key=lambda node, ctx: str(hash(node)),
    ttl=timedelta(minutes=5),
    serializer=PydanticSerializer(instance_of=SomeModel),
)
```

For JSON-compatible scalars, [MsgSpecScalarSerializer](msgspec.md) is lighter. Choose `PydanticSerializer` when you need schema validation on read.

## See also

- [Pydantic cookbook](../cookbook/pydantic.md) — end-to-end API scenario
- [MsgSpec serialization](msgspec.md) — fast scalar encoding for Redis cache
