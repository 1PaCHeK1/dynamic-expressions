from collections.abc import Callable
from functools import reduce
from typing import Any

import pytest
from dynamic_expressions.context.expression import Expression, node_of
from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    LiteralNode,
    Node,
    UnaryExpressionNode,
)

type BinaryBuilder = Callable[[Expression[Any], Expression[Any]], Expression[Any]]


def lit(value: object) -> LiteralNode:
    return LiteralNode(value=value)


def expr(value: object) -> Expression[Any]:
    return Expression(lit(value))


def assert_combined(
    node: Node,
    combiner: type[AllOfNode | AnyOfNode],
    *values: object,
) -> None:
    assert isinstance(node, combiner)
    assert node.expressions == tuple(lit(value) for value in values)


def combine(op: str, *values: object) -> Expression[Any]:
    expressions = [expr(value) for value in values]
    return reduce(
        (lambda left, right: left & right)
        if op == "&"
        else (lambda left, right: left | right),
        expressions,
    )


@pytest.mark.parametrize(
    ("other", "expected"),
    [
        (expr(1), lit(1)),
        (lit(2), lit(2)),
        (3, lit(3)),
    ],
)
def test_node_of(other: object, expected: LiteralNode) -> None:
    assert node_of(other) == expected


def test_node_property_repr_and_hash() -> None:
    node = lit(1)
    expression = Expression[object](node)

    assert expression.node is node
    assert repr(expression) == f"Expression({node!r})"
    assert hash(expression) == hash(Expression(node))


def test_in_() -> None:
    node = expr(1).in_((1, 2, 3)).node
    assert isinstance(node, BinaryExpressionNode)
    assert node.operator == "in"
    assert node.left == lit(1)
    assert node.right == lit((1, 2, 3))


@pytest.mark.parametrize(
    ("apply_unary", "operator"),
    [
        (lambda expression: +expression, "+"),
        (lambda expression: -expression, "-"),
        (lambda expression: ~expression, "~"),
        (abs, "abs"),
    ],
)
def test_unary(
    apply_unary: Callable[[Expression[Any]], Expression[Any]],
    operator: str,
) -> None:
    node = apply_unary(expr(1)).node
    assert isinstance(node, UnaryExpressionNode)
    assert node.operator == operator
    assert node.value == lit(1)


@pytest.mark.parametrize(
    ("builder", "operator"),
    [
        (lambda left, right: left == right, "="),
        (lambda left, right: left != right, "!="),
        (lambda left, right: left < right, "<"),
        (lambda left, right: left <= right, "<="),
        (lambda left, right: left > right, ">"),
        (lambda left, right: left >= right, ">="),
        (lambda left, right: left + right, "+"),
        (lambda left, right: left - right, "-"),
        (lambda left, right: left * right, "*"),
        (lambda left, right: left / right, "/"),
        (lambda left, right: left // right, "//"),
        (lambda left, right: left % right, "%"),
        (lambda left, right: left**right, "^"),
    ],
)
def test_binary(builder: BinaryBuilder, operator: str) -> None:
    node = builder(expr(10), expr(2)).node
    assert isinstance(node, BinaryExpressionNode)
    assert node.operator == operator
    assert node.left == lit(10)
    assert node.right == lit(2)


@pytest.mark.parametrize(
    ("expression", "operator", "left", "right"),
    [
        (2 + expr(3), "+", 2, 3),
        (10 - expr(3), "-", 10, 3),
        (4 * expr(3), "*", 4, 3),
        (8 / expr(2), "/", 8, 2),
        (9 // expr(2), "//", 9, 2),
        (10 % expr(3), "%", 10, 3),
        (2 ** expr(3), "^", 2, 3),
    ],
)
def test_reverse_binary(
    expression: Expression[Any],
    operator: str,
    left: object,
    right: object,
) -> None:
    node = expression.node
    assert isinstance(node, BinaryExpressionNode)
    assert node.operator == operator
    assert node.left == lit(left)
    assert node.right == lit(right)


@pytest.mark.parametrize(
    ("op", "combiner", "values"),
    [
        ("&", AllOfNode, (1, 2)),
        ("&", AllOfNode, (1, 2, 3)),
        ("|", AnyOfNode, (1, 2)),
        ("|", AnyOfNode, (1, 2, 3)),
    ],
)
def test_combine(
    op: str,
    combiner: type[AllOfNode | AnyOfNode],
    values: tuple[int, ...],
) -> None:
    assert_combined(combine(op, *values).node, combiner, *values)


@pytest.mark.parametrize(
    ("expression", "combiner", "values"),
    [
        (lit(1) & expr(2), AllOfNode, (1, 2)),
        (expr(1) & lit(2), AllOfNode, (1, 2)),
        (lit(1) | expr(2), AnyOfNode, (1, 2)),
        (Expression(lit(1)) | expr(2), AnyOfNode, (1, 2)),
    ],
)
def test_combine_with_mixed_operands(
    expression: Expression[Any],
    combiner: type[AllOfNode | AnyOfNode],
    values: tuple[int, ...],
) -> None:
    assert_combined(expression.node, combiner, *values)


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        (
            lit(1) & expr(2) | 3,
            AnyOfNode(
                expressions=(
                    AllOfNode(
                        expressions=(
                            lit(1),
                            lit(2),
                        ),
                    ),
                    lit(3),
                ),
            ),
        ),
        (
            expr(1) & (expr(2) | 3),
            AllOfNode(
                expressions=(
                    lit(1),
                    AnyOfNode(
                        expressions=(
                            lit(2),
                            lit(3),
                        ),
                    ),
                ),
            ),
        ),
        (
            (expr(1) & expr(2)) | (expr(3) & expr(4)),
            AnyOfNode(
                expressions=(
                    AllOfNode(
                        expressions=(
                            lit(1),
                            lit(2),
                        ),
                    ),
                    AllOfNode(
                        expressions=(
                            lit(3),
                            lit(4),
                        ),
                    ),
                ),
            ),
        ),
        (
            (expr(1) | expr(2)) & (expr(3) | expr(4)),
            AllOfNode(
                expressions=(
                    AnyOfNode(
                        expressions=(
                            lit(1),
                            lit(2),
                        ),
                    ),
                    AnyOfNode(
                        expressions=(
                            lit(3),
                            lit(4),
                        ),
                    ),
                ),
            ),
        ),
    ],
)
def test_complex_expression(
    expression: Expression[Any],
    result: AllOfNode | AnyOfNode,
) -> None:
    assert expression.node == result
