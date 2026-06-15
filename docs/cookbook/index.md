# Cookbook

Practical recipes for building, evaluating, serializing, and caching expressions.

Each section walks through a realistic scenario inspired by the test suite, but pressented in code you can adapt in an application.

## Sections

- **[Basic](basic.md)** — define a typed context, compose rules with the DSL, and evaluate them with a dispatcher.
- **[AST](ast.md)** — parse expression strings into node trees and read fields from the context.
- **[AST + Context](ast-context.md)** — merge database rules parsed from strings with static DSL checks.
- **[Pydantic](pydantic.md)** — store expressions as JSON, validate them with Pydantic, and convert back to nodes.
- **[Cache](cache.md)** — cache expensive node results in Redis between evaluations.

## Optional dependencies

Some recipes require extras from `pyproject.toml`:

```bash
pip install dynamic-expressions[serialization-pydantic]   # Pydantic recipe
pip install dynamic-expressions[cache-redis,serialization-msgspec]  # Cache recipe
```
