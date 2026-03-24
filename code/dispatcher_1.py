from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.types import EmptyContext
from dynamic_expressions.nodes import (
    AllOfNode,
    AnyOfNode,
    BinaryExpressionNode,
    CoalesceNode,
    LiteralNode,
    MatchNode,
)
from dynamic_expressions.visitors import (
    AllOfVisitor,
    AnyOfVisitor,
    BinaryExpressionVisitor,
    CoalesceVisitor,
    LiteralVisitor,
    MatchVisitor,
)


def create_dispatcher() -> VisitorDispatcher[EmptyContext]:
    return VisitorDispatcher[EmptyContext](
        visitors={
            AllOfNode: AllOfVisitor(),
            AnyOfNode: AnyOfVisitor(),
            BinaryExpressionNode: BinaryExpressionVisitor(),
            LiteralNode: LiteralVisitor(),
            CoalesceNode: CoalesceVisitor(),
            MatchNode: MatchVisitor(),
        },
    )


async def main() -> None:
    dispatcher = create_dispatcher()
    node = BinaryExpressionNode(
        operator="+",
        left=LiteralNode(value=1),
        right=LiteralNode(value=2),
    )
    result = await dispatcher.visit(node, None)
    assert result == 3
