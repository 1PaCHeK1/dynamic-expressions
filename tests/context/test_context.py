import pytest
from dynamic_expressions.context import Context, Mapped, mapped_field
from dynamic_expressions.context.operators import not_
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    FromContextNode,
    LiteralNode,
    UnaryExpressionNode,
)
from dynamic_expressions.visitors import (
    AllOfVisitor,
    AnyOfVisitor,
    BinaryExpressionVisitor,
    FromContextNodeVisitor,
    LiteralVisitor,
    UnaryExpressionVisitor,
)


class UserContext(Context):
    is_admin: Mapped[bool]
    division_id: Mapped[int]
    grade_level: Mapped[int]


class UserContextWithDefaults(Context):
    is_admin: Mapped[bool] = mapped_field(default_factory=lambda: False)
    division_id: Mapped[int] = mapped_field(default=1)


@pytest.fixture
def dispatcher() -> VisitorDispatcher[UserContext]:
    return VisitorDispatcher[UserContext](
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            LiteralNode: LiteralVisitor(),
            FromContextNode: FromContextNodeVisitor(),
            UnaryExpressionNode: UnaryExpressionVisitor(),
        },
    )


def test_field_access_builds_from_context_node() -> None:
    expression = UserContext.is_admin
    assert isinstance(expression.node, FromContextNode)
    assert expression.node.field_name == "is_admin"


def test_context_respects_field_defaults() -> None:
    assert UserContextWithDefaults().is_admin is False
    assert UserContextWithDefaults().division_id == 1


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        (UserContext(is_admin=True, division_id=1, grade_level=1), False),
        (UserContext(is_admin=False, division_id=1, grade_level=1), True),
    ],
)
async def test_visit_not(
    dispatcher: VisitorDispatcher[UserContext],
    context: UserContext,
    expected: bool,
) -> None:
    expression = not_(UserContext.is_admin)
    assert await dispatcher.visit(expression, context) is expected


def test_complex_expression() -> None:
    expression = UserContext.is_admin | (
        UserContext.division_id.in_((1, 2, 3)) & (UserContext.grade_level > 3)
    )
    node = expression.node
    assert isinstance(node, AnyOfNode)
    assert isinstance(node.expressions[0], FromContextNode)
    assert isinstance(node.expressions[1], AllOfNode)
    in_node = node.expressions[1].expressions[0]
    assert isinstance(in_node, BinaryExpressionNode)
    assert in_node.operator == "in"
    gt_node = node.expressions[1].expressions[1]
    assert isinstance(gt_node, BinaryExpressionNode)
    assert gt_node.operator == ">"


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        (UserContext(is_admin=True, division_id=99, grade_level=1), True),
        (UserContext(is_admin=False, division_id=2, grade_level=5), True),
        (UserContext(is_admin=False, division_id=99, grade_level=5), False),
        (UserContext(is_admin=False, division_id=2, grade_level=2), False),
    ],
)
async def test_visit_complex_expression(
    dispatcher: VisitorDispatcher[UserContext],
    context: UserContext,
    expected: bool,
) -> None:
    expression = UserContext.is_admin | (
        UserContext.division_id.in_((1, 2, 3)) & (UserContext.grade_level > 3)
    )
    assert await dispatcher.visit(expression, context) is expected
