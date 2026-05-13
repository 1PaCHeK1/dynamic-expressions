import pytest
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import BinaryExpressionNode, LiteralNode
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


@pytest.mark.parametrize("left", random_numbers)
@pytest.mark.parametrize("right", random_numbers)
async def test_add(
    left: LiteralNode,
    right: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = BinaryExpressionNode(operator="+", left=left, right=right)
    assert await dispatcher.visit(node, None) == (left.value + right.value)


@pytest.mark.parametrize("left", random_numbers)
@pytest.mark.parametrize("right", random_numbers)
async def test_eq(
    left: LiteralNode,
    right: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = BinaryExpressionNode(operator="=", left=left, right=right)
    assert await dispatcher.visit(node, None) == (left.value == right.value)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (0, 63, 0),
        (5, 4, 4),
        (8, 4, 0),
    ],
)
async def test_binary_and(
    dispatcher: VisitorDispatcher[EmptyContext], left: int, right: int, expected: int
) -> None:
    node = BinaryExpressionNode(
        operator="&", left=LiteralNode(left), right=LiteralNode(right)
    )
    assert await dispatcher.visit(node, None) == expected == (left & right)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (pytest, "mark", pytest.mark),
        (pytest, "mark.parametrize", pytest.mark.parametrize),
        (pytest, "mark.parametrize.markname", pytest.mark.parametrize.markname),
    ],
)
async def test_getattr(
    dispatcher: VisitorDispatcher[EmptyContext],
    left: object,
    right: str,
    expected: object,
) -> None:
    node = BinaryExpressionNode(
        operator="getattr", left=LiteralNode(left), right=LiteralNode(right)
    )
    assert await dispatcher.visit(node, None) == expected


async def test_in_warning(
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = BinaryExpressionNode(
        operator="in", left=LiteralNode(value=(1, 2, 3)), right=LiteralNode(1)
    )
    with pytest.warns(
        DeprecationWarning,
        match=(
            r'BinaryExpressionNode\(operator="in", left=<container>, right=<search value>\) is depricated, '
            r'use BinaryExpressionNode\(operator="in", left=<search value>, right=<container>\)'
        ),
    ):
        assert await dispatcher.visit(node, None)


@pytest.mark.parametrize(
    "left",
    [LiteralNode(1), LiteralNode((1, 2))],
)
async def test_in_without_warning(
    left: LiteralNode,
    dispatcher: VisitorDispatcher[EmptyContext],
) -> None:
    node = BinaryExpressionNode(
        operator="in",
        left=left,
        right=LiteralNode((1, 2, 3, (1, 2))),
    )
    assert await dispatcher.visit(node, None)
