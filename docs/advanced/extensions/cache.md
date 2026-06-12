
## CacheExtension

Base class for persistent caching. Before a node is evaluated, the extension looks up a cache key; on a hit, the result is stored in `ExecutionContext.cache` and the visitor is skipped.

::: dynamic_expressions.cache.base.CacheExtension

### CachePolicy

A policy defines which node types to cache, how to build keys, and TTL:

::: dynamic_expressions.cache.base.CachePolicy

| Field | Description |
|-------|-------------|
| `types` | Tuple of node classes this policy applies to |
| `key` | Callable `(node, context) -> str` — cache key builder |
| `ttl` | `timedelta` — entry lifetime in the backing store |
| `serializer` | Optional per-policy serializer; falls back to `default_serializer` |

```python
from datetime import timedelta

from dynamic_expressions.cache import CachePolicy
from dynamic_expressions.nodes import LiteralNode

policy = CachePolicy[MyContext](
    types=(LiteralNode,),
    key=lambda node, ctx: str(hash(node)),
    ttl=timedelta(minutes=5),
)
```

When results depend on context, include context fields in the key:

```python
CachePolicy[UserContext](
    types=(BinaryExpressionNode,),
    key=lambda node, ctx: f"{hash(node)}:{ctx.user_id}",
    ttl=timedelta(minutes=5),
)
```

### RedisCacheExtension

Redis-backed implementation. Requires `pip install dynamic-expressions[cache-redis,serialization-msgspec]`.

::: dynamic_expressions.cache.redis.RedisCacheExtension

See the [Cache cookbook](../cookbook/cache.md) for a full wiring example.

## Writing a custom backend

Subclass `CacheExtension` and implement `get_cache` / `set_cache`:

```python
class InMemoryCacheExtension[Context](CacheExtension[Context]):
    def __init__(
        self,
        policies: Sequence[CachePolicy[Context]],
        default_serializer: Serializer[Any],
    ) -> None:
        self.policies = policies
        self.default_serializer = default_serializer
        self._policy_cache = {}
        self._store = {}

    async def get_cache(self, key: str) -> bytes | None:
        return self._store.get(key)

    async def set_cache(self, key: str, value: bytes, policy: CachePolicy[Context]) -> None:
        self._store[key] = value
```

Use a [Serializer](../serialization/index.md) compatible with your cached value types.
