# Cache

Skip repeated work when the same node is evaluated many times with identical context.

Install optional dependencies:

```bash
pip install dynamic-expressions[cache-redis,serialization-msgspec]
```

You also need a running Redis-compatible server (Valkey works too).

!!! warning "Cache narrow bottlenecks"
    Caching every node type in a deep tree is usually a bad idea: keys multiply, Redis fills up, and stale data becomes hard to reason about. Prefer a dedicated node for expensive steps and list **only that type** in `CachePolicy.types`. Cheap nodes (`LiteralNode`, comparisons, boolean glue) should stay uncached.


## How caching behaves

1. Before a node is visited, `RedisCacheExtension` looks up a cache key produced by the matching [CachePolicy](../advanced/extensions/cache.md#cachepolicy).
2. On a hit, the deserialized value is stored in the per-call `ExecutionContext` cache and visitors are skipped for that node.
3. After evaluation, changed results are written back to Redis with the configured TTL.

Policies are matched by node type. Use a custom `key` when the same node shape must produce different cache entries for different contexts:

```python
CachePolicy[YourContext](
    types=(SomeNode,),
    key=lambda node, ctx: f"folder:{hash(node.node)}:{ctx.user_id}",
    ttl=timedelta(minutes=5),
)
```

Provide a dedicated `serializer` on the policy when cached values are not plain scalars.


## Scenario

A discount service evaluates a dynamic rule on every checkout. Results depend only on the node structure, not on request context, so they are safe to cache in Redis for a short TTL.

The example below caches all standard node types — useful to show wiring, but **not** how you should structure production policies. See [Targeted caching](#targeted-caching-with-cachenode) for the recommended approach.

## Wire Redis into the dispatcher

```python
def build_dispatcher(client: RedisClient) -> VisitorDispatcher[EmptyContext]:
    return VisitorDispatcher(
        visitors={...},
        extensions=[
            RedisCacheExtension(
                client=client,
                policies=[
                    CachePolicy[EmptyContext](
                        types=(
                            BinaryExpressionNode,
                            LiteralNode,
                        ),
                        key=lambda node, _: str(hash(node)),
                        ttl=timedelta(seconds=60),
                    ),
                ],
                default_serializer=MsgSpecScalarSerializer(),
            ),
        ],
    )


async def get_discount_rule() -> Node:
    return BinaryExpressionNode(
        operator="+",
        left=LiteralNode(value=1.0),
        right=LiteralNode(value=12.0),
    )


async def main() -> None:
    client = redis.Redis(host="localhost", port=6379, decode_responses=False)
    dispatcher = build_dispatcher(client)

    discount_rule = await get_discount_rule()

    first = await dispatcher.visit(discount_rule, None)
    second = await dispatcher.visit(discount_rule, None)

    assert first is True
    assert second is True  # served from Redis on the second call

    await client.aclose()


asyncio.run(main())
```

## Targeted caching with CacheNode

Wrap only the expensive step in a `CacheNode` that holds the inner expression in `node`. Register a matching visitor and a `CachePolicy` that lists **just** `CacheNode`.

```python
@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class CacheNode(Node):
    """Marks an expensive lookup; only this type is cached in Redis."""

    node: Node


class CacheVisitor(Visitor[CacheNode, EmptyContext]):
    async def visit(
        self,
        *,
        node: CacheNode,
        dispatch: Dispatch[EmptyContext],
        context: EmptyContext,
    ) -> Any:
        return await dispatch(node.node, context)


@dataclass(slots=True, frozen=True, kw_only=True, unsafe_hash=True)
class FetchPriceNode(Node):
    product_id: str


class FetchPriceVisitor(Visitor[FetchPriceNode, PricingContext]):
    async def visit(
        self,
        *,
        node: FetchPriceNode,
        dispatch: Dispatch[PricingContext],
        context: PricingContext,
    ) -> float:
        # Stand in for a slow HTTP/RPC call
        await asyncio.sleep(0.5)
        base = {"eu": 100.0, "us": 120.0}[context.region]
        return base + await fetch_price(node.product_id)


@dataclass(slots=True, frozen=True, kw_only=True)
class PricingContext:
    region: str


def build_dispatcher(client: RedisClient) -> VisitorDispatcher[PricingContext]:
    return VisitorDispatcher(
        visitors={
            ...,
            FetchPriceNode: FetchPriceVisitor(),
            CacheNode: CacheVisitor(),
        },
        extensions=[
            RedisCacheExtension(
                client=client,
                policies=[
                    CachePolicy[PricingContext](
                        types=(CacheNode,),
                        key=lambda node, ctx: f"cache:{hash(node.node)}:{ctx.region}",
                        ttl=timedelta(minutes=10),
                    ),
                ],
                default_serializer=MsgSpecScalarSerializer(),
            ),
        ],
    )


compute_price_rule = MatchNode(
    cases=(
        CaseNode(
            expression=BinaryExpressionNode(
                operator="=",
                left=FromContextNode(field_name="region"),
                right=LiteralNode(value="de"),
            ),
            value=LiteralNode(value=100),
        ),
        default=CacheNode(
            node=CoalesceNode(
                items=(
                    FetchPriceNode(product_id="pixel-9-sale"),
                    FetchPriceNode(product_id="pixel-9"),
                ),
            ),
        ),
    ),
)


async def main() -> None:
    client = redis.Redis(host="localhost", port=6379, decode_responses=False)
    dispatcher = build_dispatcher(client)
    context = PricingContext(region="eu")

    first = await dispatcher.visit(compute_price_rule, context)
    second = await dispatcher.visit(compute_price_rule, context)

    assert first == second  # CacheNode result reused from Redis
    await client.aclose()


asyncio.run(main())
```

`MatchNode`, comparisons, and context reads are evaluated on every request. Redis stores only the `CacheNode` result keyed by the wrapped subtree (`node.node`) and region.

On a cache hit, `CacheVisitor` is skipped — the inner `FetchPriceNode` is not evaluated again.
