from __future__ import annotations

import dataclasses
import typing
from dataclasses import MISSING
from typing import (
    TYPE_CHECKING,
    Any,
    overload,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from dynamic_expressions.context.expression import Expression


if TYPE_CHECKING:

    class Mapped[T]:
        @overload
        def __get__(self, obj: None, owner: type[Any]) -> Expression[T]: ...

        @overload
        def __get__(self, obj: object, owner: type[Any]) -> T: ...

        def __get__(self, obj: object | None, owner: type[Any]) -> Expression[T] | T:
            raise NotImplementedError

        def __set__(self, instance: object, value: T) -> None:
            raise NotImplementedError
else:
    type Mapped[T] = T


def is_mapped_annotation(annotation: object) -> bool:
    if isinstance(annotation, str):
        return annotation.startswith("Mapped[")
    origin = typing.get_origin(annotation)
    if origin is Mapped:
        return True
    return isinstance(origin, type)


def mapped_inner_type(annotation: object) -> object:
    if isinstance(annotation, str):
        msg = "Mapped annotation must be resolved before building the dataclass"
        raise TypeError(msg)
    args = typing.get_args(annotation)
    if args:
        return args[0]
    return annotation


@overload
def mapped_field[T](*, default: T) -> Mapped[T]: ...


@overload
def mapped_field[T](*, default_factory: Callable[[], T]) -> Mapped[T]: ...


def mapped_field(
    *,
    default: object = MISSING,
    default_factory: Callable[[], object] | object = MISSING,
) -> object:
    """Like :func:`dataclasses.field`, for use with :data:`Mapped` annotations."""
    if default_factory is not MISSING:
        factory = typing.cast("Callable[[], object]", default_factory)
        return dataclasses.field(default_factory=factory)
    if default is not MISSING:
        return dataclasses.field(default=default)
    return dataclasses.field()
