from collections.abc import Iterable, Mapping
from typing import Any, overload

from dynamic_expressions import nodes
from dynamic_expressions.context.expression import AnyExpression, Expression, node_of


def not_(expression: AnyExpression[Any]) -> Expression[bool]:
    return Expression(
        nodes.UnaryExpressionNode(
            operator="not",
            value=node_of(expression),
        ),
    )


def and_(*expressions: AnyExpression[Any]) -> Expression[bool]:
    return Expression(
        node=nodes.AllOfNode(expressions=tuple(node_of(i) for i in expressions))
    )


def or_(*expressions: AnyExpression[Any]) -> Expression[bool]:
    return Expression(
        node=nodes.AnyOfNode(expressions=tuple(node_of(i) for i in expressions))
    )


def coalesce[T](*expressions: AnyExpression[T]) -> Expression[T]:
    return Expression(
        node=nodes.CoalesceNode(items=tuple(node_of(i) for i in expressions))
    )


@overload
def match(
    cases: Mapping[AnyExpression[Any], AnyExpression[Any]],
    *,
    value: AnyExpression[Any],
    default: AnyExpression[Any] | None = None,
) -> Expression[Any]: ...


@overload
def match(
    cases: Iterable[tuple[AnyExpression[Any], AnyExpression[Any]]],
    *,
    default: AnyExpression[Any] | None = None,
) -> Expression[Any]: ...


@overload
def match(
    cases: Mapping[AnyExpression[Any], AnyExpression[Any]],
    *,
    default: AnyExpression[Any] | None = None,
) -> Expression[Any]: ...


def match(
    cases: (
        Mapping[AnyExpression[Any], AnyExpression[Any]]
        | Iterable[tuple[AnyExpression[Any], AnyExpression[Any]]]
    ),
    *,
    value: AnyExpression[Any] | None = None,
    default: AnyExpression[Any] | None = None,
) -> Expression[Any]:
    if isinstance(cases, Mapping):
        cases = cases.items()
    if value:
        cases = tuple(
            (
                nodes.BinaryExpressionNode(
                    operator="=", left=node_of(value), right=node_of(key)
                ),
                value_,
            )
            for key, value_ in cases
        )

    return Expression(
        node=nodes.MatchNode(
            cases=tuple(
                nodes.CaseNode(expression=node_of(k), value=node_of(v))
                for k, v in cases
            ),
            default=node_of(default) if default is not None else None,
        ),
    )
