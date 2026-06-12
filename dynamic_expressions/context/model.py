from __future__ import annotations

import dataclasses
import typing
from dataclasses import MISSING
from typing import Any, dataclass_transform

from dynamic_expressions.context.expression import Expression
from dynamic_expressions.context.mapped import (
    is_mapped_annotation,
    mapped_field,
    mapped_inner_type,
)
from dynamic_expressions.nodes import FromContextNode


class _ContextMeta(type):
    def __getattribute__(cls, name: str) -> object:
        if name.startswith("__"):
            return type.__getattribute__(cls, name)
        fields = type.__getattribute__(cls, "__dict__").get("__dataclass_fields__")
        if fields is not None and name in fields:
            return Expression(FromContextNode(field_name=name))
        return type.__getattribute__(cls, name)

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if name == "Context":
            return super().__new__(mcs, name, bases, namespace, **kwargs)

        raw_annotations = typing.cast("dict[str, object]", namespace["__annotations__"])
        has_mapped_fields = any(
            is_mapped_annotation(annotation) for annotation in raw_annotations.values()
        )
        if not has_mapped_fields:
            return super().__new__(mcs, name, bases, namespace, **kwargs)

        prepared = _prepare_subclass_namespace(namespace)
        cls = super().__new__(mcs, name, bases, prepared, **kwargs)
        decorated: Any = dataclasses.dataclass(
            slots=True,
            frozen=True,
            kw_only=True,
            unsafe_hash=True,
        )
        return typing.cast("type[Any]", decorated(cls))


def _prepare_subclass_namespace(  # noqa: C901
    namespace: dict[str, object],
) -> dict[str, object]:
    raw_annotations = typing.cast("dict[str, object]", namespace["__annotations__"])
    prepared = dict(namespace)

    for key, value in namespace.items():
        if key in raw_annotations:
            continue
        prepared[key] = value

    for field_name, annotation in raw_annotations.items():
        if not is_mapped_annotation(annotation):
            continue
        raw = namespace.get(field_name, MISSING)
        if raw is MISSING:
            prepared[field_name] = dataclasses.field()
        elif isinstance(raw, dataclasses.Field):
            prepared[field_name] = raw
        else:
            prepared[field_name] = dataclasses.field(default=raw)

    prepared["__annotations__"] = {
        name: mapped_inner_type(raw_annotations[name]) for name in raw_annotations
    }
    return prepared


@dataclass_transform(
    eq_default=True,
    order_default=False,
    kw_only_default=True,
    frozen_default=True,
    field_specifiers=(mapped_field,),
)
class Context(metaclass=_ContextMeta):
    """Base class for DSL contexts. Subclass with :data:`Mapped` fields."""
