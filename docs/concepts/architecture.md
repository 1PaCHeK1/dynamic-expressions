# Architecture

**Dynamic-expressions** separate what an expression is (nodes) from the way it is evaluated (visitors). A dispatcher connects these two aspects and provides hooks for caching, middleware, and serialization.

## Core model

```mermaid
flowchart LR
    dsl[Context DSL] -->|.node| nodes[Node tree]
    ast[AST parser] --> nodes
    pydantic[Pydantic JSON] -->|".to_node()"| nodes
    nodes --> visit[dispatcher.visit]
```

Nodes describe the structure; visitors evaluate it. The dispatcher maps node types to visitors and runs hooks around each evaluation step.

## Building expressions

There are three common ways to obtain a node tree:

| Approach | When to use |
|----------|-------------|
| [Context DSL](context-dsl.md) | Rules authored in Python with type-safe field access |
| [AST parser](../serialization/ast.md) | Rules stored as strings in config or a database |
| [Pydantic schemas](../serialization/pydantic.md) | Rules exchanged as JSON over an API or retrieved from the database |

All paths produce the same immutable `Node` trees evaluated by the dispatcher.

## Evaluation pipeline

Each `await dispatcher.visit(node, context)` creates an `ExecutionContext`. Every node — the root and each child visited via `dispatch()` — goes through the same steps shown below.

```mermaid
sequenceDiagram
    participant Caller
    participant Disp as VisitorDispatcher
    participant Ext as Extension
    participant MW as Middleware
    participant Visitor

    Caller->>Disp: visit(node, context)

    loop each node
        Disp->>Ext: enter on_visit(node,context,execution_context)
        Note over Ext: wraps cache check, middleware, and visitor

        Disp->>MW: on_visit with call_next
        MW->>Visitor: visit via call_next
        Visitor-->>MW: result
        MW-->>Disp: result

        opt child nodes
            Visitor->>Disp: dispatch(child_node, context)
            Note over Disp: same pipeline for each child
        end

        Ext-->>Disp: exit on_visit()
    end

    Disp-->>Caller: result
```

When you call `await dispatcher.visit(node, context)`:

1. **Extensions** — each registered `OnVisitExtension` enters an async context manager that wraps the rest of the node scope.
2. **Per-call cache** — if the node was already evaluated in this `visit` call, return the memoized result.
3. **Middlewares** — optional chain that wraps the call to `Visitor.visit`. Each middleware receives `call_next` and invokes the next layer (another middleware, or the visitor at the end of the chain).
4. **Visitor** — `Visitor.visit(node, dispatch, context)` evaluates the node. Composite visitors call `dispatch(child, context)`, which re-enters `VisitorDispatcher._visit` for each child with the full pipeline above.
5. **Store result** — the return value is cached in `ExecutionContext` for the remainder of the call.

## Context

**Context** is runtime input data — a dataclass instance, a Pydantic model, or any object with attributes. [FromContextNode](nodes.md#from-context) reads fields from it during evaluation.

**ExecutionContext** is internal per-call state (currently a node→result cache). Extensions may read or pre-populate it.

## Serialization and caching

- [Serialization](../serialization/index.md) converts node trees to/from bytes or JSON for storage and transport.
- [Cache extensions](../advanced/extensions/index.md) persist evaluation results in Redis (or a custom backend) across requests.

## Next steps

- [Getting started](../getting-started.md) — minimal working example
- [Nodes reference](nodes.md) — all built-in node types
- [Cookbook](../cookbook/index.md) — end-to-end recipes
