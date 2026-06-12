from dynamic_expressions.context.expression import Expression
from dynamic_expressions.context.operators import and_, coalesce, match, not_, or_
from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    CaseNode,
    CoalesceNode,
    LiteralNode,
    MatchNode,
    UnaryExpressionNode,
)


def lit(value: object) -> LiteralNode:
    return LiteralNode(value=value)


def expr[T](value: T) -> Expression[T]:
    return Expression(lit(value))


def test_not_operator() -> None:
    node = not_(expr(1)).node
    assert isinstance(node, UnaryExpressionNode)
    assert node.operator == "not"
    assert node.value == lit(1)


def test_not_operator_accepts_literal() -> None:
    node = not_(0).node
    assert isinstance(node, UnaryExpressionNode)
    assert node.value == lit(0)


def test_and_operator() -> None:
    node = and_(expr(1), LiteralNode(2), 3).node
    assert isinstance(node, AllOfNode)
    assert node.expressions == (lit(1), lit(2), lit(3))


def test_or_operator() -> None:
    node = or_(expr(1), LiteralNode(2), 3).node
    assert isinstance(node, AnyOfNode)
    assert node.expressions == (lit(1), lit(2), lit(3))


def test_coalesce_operator() -> None:
    node = coalesce(expr(1), lit(2), 3).node
    assert isinstance(node, CoalesceNode)
    assert node.items == (lit(1), lit(2), lit(3))


def test_match_from_iterable() -> None:
    node = match([(1, expr(10)), (lit(2), lit(20))]).node
    assert isinstance(node, MatchNode)
    assert node.default is None
    assert node.cases == (
        CaseNode(expression=lit(1), value=lit(10)),
        CaseNode(expression=lit(2), value=lit(20)),
    )


def test_match_from_mapping() -> None:
    node = match({expr(1): expr(10), expr(2): expr(20)}).node
    assert isinstance(node, MatchNode)
    assert node.default is None
    assert node.cases == (
        CaseNode(expression=lit(1), value=lit(10)),
        CaseNode(expression=lit(2), value=lit(20)),
    )


def test_match_with_default() -> None:
    node = match([(expr(1), expr(10))], default=expr(0)).node
    assert isinstance(node, MatchNode)
    assert node.default == lit(0)
    assert node.cases == (CaseNode(expression=lit(1), value=lit(10)),)


def test_match_with_value_builds_equality_cases() -> None:
    expression = match({expr(1): expr(10), expr(2): expr(20)}, value=5)
    node = expression.node
    assert isinstance(node, MatchNode)
    assert node.cases == (
        CaseNode(
            expression=BinaryExpressionNode(
                operator="=",
                left=lit(5),
                right=lit(1),
            ),
            value=lit(10),
        ),
        CaseNode(
            expression=BinaryExpressionNode(
                operator="=",
                left=lit(5),
                right=lit(2),
            ),
            value=lit(20),
        ),
    )
