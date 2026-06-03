import operator

import pytest
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import LiteralNode, UnaryExpressionNode
from dynamic_expressions.types import EmptyContext

random_numbers: list[LiteralNode] = [
    LiteralNode(value=0),
    LiteralNode(value=1),
    LiteralNode(value=3),
    LiteralNode(value=100),
    LiteralNode(value=-1),
    LiteralNode(value=-3),
    LiteralNode(value=-100),
]


@pytest.mark.parametrize("value", random_numbers)
async def test_pos(
    value: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="+", value=value)
    assert await dispatcher.visit(node, None) == operator.pos(value.value)


@pytest.mark.parametrize("value", random_numbers)
async def test_neg(
    value: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="-", value=value)
    assert await dispatcher.visit(node, None) == operator.neg(value.value)


@pytest.mark.parametrize("value", random_numbers)
async def test_inv(
    value: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="~", value=value)
    assert await dispatcher.visit(node, None) == operator.inv(value.value)


@pytest.mark.parametrize("value", random_numbers)
async def test_abs(
    value: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="abs", value=value)
    assert await dispatcher.visit(node, None) == operator.abs(value.value)


@pytest.mark.parametrize(
    "value",
    [
        LiteralNode(value=0),
        LiteralNode(value=1),
        LiteralNode(value=""),
        LiteralNode(value="abc"),
        LiteralNode(value=None),
        LiteralNode(value=()),
    ],
)
async def test_not(
    value: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="not", value=value)
    assert await dispatcher.visit(node, None) == operator.not_(value.value)


async def test_unknown_operator(
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = UnaryExpressionNode(operator="unknown", value=LiteralNode(1))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"Unknown operator 'unknown'"):
        await dispatcher.visit(node, None)
