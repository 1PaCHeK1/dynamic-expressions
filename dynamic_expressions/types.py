from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from dynamic_expressions.nodes import Node


class EmptyContext(Protocol): ...


@dataclass
class ExecutionContext:
    cache: dict[Node, Any] = field(default_factory=dict)


UnaryExpressionOperator = Literal[
    "+",
    "-",
    "~",
    "abs",
    "not",
]


BinaryExpressionOperator = Literal[
    "=",
    ">",
    ">=",
    "<",
    "<=",
    "!=",
    "in",
    "+",
    "-",
    "*",
    "/",
    "//",
    "%",
    "^",
    "&",
    "|",
    "getitem",
    "getattr",
]
