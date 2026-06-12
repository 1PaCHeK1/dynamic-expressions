import pytest
from dynamic_expressions.dispatcher import VisitorDispatcher
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
from dynamic_expressions.types import EmptyContext
from dynamic_expressions.visitors import (
    AllOfVisitor,
    AnyOfVisitor,
    BinaryExpressionVisitor,
    CaseVisitor,
    CoalesceVisitor,
    LiteralVisitor,
    MatchVisitor,
    UnaryExpressionVisitor,
)

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session", autouse=True)
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def dispatcher() -> VisitorDispatcher[EmptyContext]:
    return VisitorDispatcher[EmptyContext](
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            UnaryExpressionNode: UnaryExpressionVisitor(),
            LiteralNode: LiteralVisitor(),
            CoalesceNode: CoalesceVisitor(),
            CaseNode: CaseVisitor(),
            MatchNode: MatchVisitor(),
        },
    )
