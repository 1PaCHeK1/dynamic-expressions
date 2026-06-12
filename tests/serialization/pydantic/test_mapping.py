from typing import Any

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
from dynamic_expressions.serialization.pydantic import (
    AllOfNodeSchema,
    AnyOfNodeSchema,
    BinaryExpressionNodeSchema,
    CaseNodeSchema,
    CoalesceNodeSchema,
    LiteralNodeSchema,
    MatchNodeSchema,
    UnaryExpressionNodeSchema,
)


def test_literal() -> None:
    value = "value"
    schema = LiteralNodeSchema[str](type="literal", value=value)

    assert schema.to_node() == LiteralNode(value=value)


def test_binary() -> None:
    schema = BinaryExpressionNodeSchema[Any](
        type="binary",
        operator="+",
        left=LiteralNodeSchema(type="literal", value=1),
        right=LiteralNodeSchema(type="literal", value=1),
    )
    node = BinaryExpressionNode(
        operator="+",
        left=LiteralNode(value=1),
        right=LiteralNode(value=1),
    )
    assert schema.to_node() == node


def test_unary() -> None:
    schema = UnaryExpressionNodeSchema[Any](
        type="unary",
        operator="-",
        value=LiteralNodeSchema(type="literal", value=1),
    )
    node = UnaryExpressionNode(
        operator="-",
        value=LiteralNode(value=1),
    )
    assert schema.to_node() == node


def test_all_of() -> None:
    schema = AllOfNodeSchema[Any](
        type="all-of",
        expressions=(
            LiteralNodeSchema(type="literal", value=True),
            LiteralNodeSchema(type="literal", value=False),
        ),
    )
    node = AllOfNode(
        expressions=(
            LiteralNode(value=True),
            LiteralNode(value=False),
        ),
    )
    assert schema.to_node() == node


def test_any_of() -> None:
    schema = AnyOfNodeSchema[Any](
        type="any-of",
        expressions=(
            LiteralNodeSchema(type="literal", value=True),
            LiteralNodeSchema(type="literal", value=False),
        ),
    )
    node = AnyOfNode(
        expressions=(
            LiteralNode(value=True),
            LiteralNode(value=False),
        ),
    )
    assert schema.to_node() == node


def test_coalesce() -> None:
    schema = CoalesceNodeSchema[Any](
        type="coalesce",
        items=(
            LiteralNodeSchema(type="literal", value=True),
            LiteralNodeSchema(type="literal", value=False),
        ),
    )
    node = CoalesceNode(
        items=(
            LiteralNode(value=True),
            LiteralNode(value=False),
        ),
    )
    assert schema.to_node() == node


def test_case() -> None:
    schema = CaseNodeSchema[Any](
        type="case",
        expression=LiteralNodeSchema(type="literal", value=True),
        value=LiteralNodeSchema(type="literal", value=False),
    )
    node = CaseNode(
        expression=LiteralNode(value=True),
        value=LiteralNode(value=False),
    )
    assert schema.to_node() == node


def test_match() -> None:
    schema = MatchNodeSchema[Any](
        type="match",
        cases=(
            CaseNodeSchema[Any](
                type="case",
                expression=LiteralNodeSchema(type="literal", value=True),
                value=LiteralNodeSchema(type="literal", value=False),
            ),
        ),
        default=LiteralNodeSchema(type="literal", value=5),
    )
    node = MatchNode(
        cases=(
            CaseNode(
                expression=LiteralNode(value=True),
                value=LiteralNode(value=False),
            ),
        ),
        default=LiteralNode(value=5),
    )
    assert schema.to_node() == node


def test_wrapped_schema() -> None:
    schema = AnyOfNodeSchema[Any](
        type="any-of",
        expressions=(
            AllOfNodeSchema(
                type="all-of",
                expressions=(
                    AnyOfNodeSchema(
                        type="any-of",
                        expressions=(
                            BinaryExpressionNodeSchema(
                                type="binary",
                                operator="+",
                                left=LiteralNodeSchema(
                                    type="literal",
                                    value=1,
                                ),
                                right=LiteralNodeSchema(
                                    type="literal",
                                    value=1,
                                ),
                            ),
                        ),
                    ),
                    BinaryExpressionNodeSchema(
                        type="binary",
                        operator="+",
                        left=LiteralNodeSchema(
                            type="literal",
                            value=1,
                        ),
                        right=LiteralNodeSchema(
                            type="literal",
                            value=1,
                        ),
                    ),
                ),
            ),
            LiteralNodeSchema(type="literal", value=False),
        ),
    )
    node = AnyOfNode(
        expressions=(
            AllOfNode(
                expressions=(
                    AnyOfNode(
                        expressions=(
                            BinaryExpressionNode(
                                operator="+",
                                left=LiteralNode(value=1),
                                right=LiteralNode(value=1),
                            ),
                        ),
                    ),
                    BinaryExpressionNode(
                        operator="+",
                        left=LiteralNode(value=1),
                        right=LiteralNode(value=1),
                    ),
                ),
            ),
            LiteralNode(value=False),
        ),
    )
    assert schema.to_node() == node
