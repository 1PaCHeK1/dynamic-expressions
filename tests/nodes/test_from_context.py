from dataclasses import dataclass

import pytest
from dynamic_expressions.dispatcher import VisitorDispatcher
from dynamic_expressions.nodes import FromContextNode, LiteralNode
from dynamic_expressions.visitors import FromContextNodeVisitor, LiteralVisitor


@dataclass
class InnerContext:
    value: int


@dataclass
class SampleContext:
    name: str
    inner: InnerContext


@pytest.fixture
def dispatcher() -> VisitorDispatcher[SampleContext]:
    return VisitorDispatcher[SampleContext](
        visitors={
            FromContextNode: FromContextNodeVisitor(),
            LiteralNode: LiteralVisitor(),
        },
    )


async def test_ok(
    dispatcher: VisitorDispatcher[SampleContext],
) -> None:
    context = SampleContext(name="alice", inner=InnerContext(value=1))
    node = FromContextNode(field_name="name")
    assert await dispatcher.visit(node, context) == "alice"


async def test_nested_field(
    dispatcher: VisitorDispatcher[SampleContext],
) -> None:
    context = SampleContext(name="alice", inner=InnerContext(value=42))
    node = FromContextNode(field_name="inner.value")
    assert await dispatcher.visit(node, context) == 42


async def test_missing_field(
    dispatcher: VisitorDispatcher[SampleContext],
) -> None:
    context = SampleContext(name="alice", inner=InnerContext(value=1))
    node = FromContextNode(field_name="missing")
    with pytest.raises(
        AttributeError,
        match=r"Field 'missing' not found in context of type 'SampleContext'",
    ):
        await dispatcher.visit(node, context)
