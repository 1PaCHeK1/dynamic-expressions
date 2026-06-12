# MsgSpec serialization

Fast JSON encoding/decoding for cache values via [msgspec](https://jcristharif.com/msgspec/).

Install the optional dependency:

```bash
pip install dynamic-expressions[serialization-msgspec]
```

## MsgSpecScalarSerializer

Used as the default serializer in [Redis cache extensions](../extending/extensions.md). Handles JSON-compatible scalars (`bool`, `int`, `float`, `str`, `None`, lists, dicts).

::: dynamic_expressions.serialization.msgspec.MsgSpecScalarSerializer

```python
from dynamic_expressions.serialization.msgspec import MsgSpecScalarSerializer

serializer = MsgSpecScalarSerializer()
payload = serializer.serialize(True)
assert serializer.deserialize(payload) is True
```

## MsgSpecSerializer

Typed serializer for a specific Python type:

::: dynamic_expressions.serialization.msgspec.MsgSpecSerializer

```python
import msgspec
from dynamic_expressions.serialization.msgspec import MsgSpecSerializer


class User(msgspec.Struct):
    name: str
    age: int


serializer = MsgSpecSerializer(instance_of=User)
user = User(name="John", age=30)

payload = serializer.serialize(user)
assert serializer.deserialize(payload) == user
```

Pass a per-policy `serializer` on [CachePolicy](../extending/extensions.md#cachepolicy) when cached values are not plain scalars.

See the [Cache cookbook](../cookbook/cache.md) for Redis integration.
