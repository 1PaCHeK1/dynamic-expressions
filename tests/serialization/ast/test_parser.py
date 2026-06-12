import pytest
from dynamic_expressions import nodes
from dynamic_expressions.serialization.ast import (
    ExpressionEvalParser,
    FromContextAttributeHandler,
    get_builtin_handlers,
)
from dynamic_expressions.serialization.ast.parser import (
    ExpressionInvalidError,
    UnknownAstNodeError,
)


@pytest.fixture
def parser() -> ExpressionEvalParser:
    return ExpressionEvalParser(
        handlers=[*get_builtin_handlers(), FromContextAttributeHandler()],
    )


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        (
            "2",
            nodes.LiteralNode(2),
        ),
        (
            "2+2",
            nodes.BinaryExpressionNode(
                operator="+",
                left=nodes.LiteralNode(2),
                right=nodes.LiteralNode(2),
            ),
        ),
        (
            "2+2*2",
            nodes.BinaryExpressionNode(
                operator="+",
                left=nodes.LiteralNode(2),
                right=nodes.BinaryExpressionNode(
                    operator="*",
                    left=nodes.LiteralNode(2),
                    right=nodes.LiteralNode(2),
                ),
            ),
        ),
        (
            "(2+2)*2",
            nodes.BinaryExpressionNode(
                operator="*",
                left=nodes.BinaryExpressionNode(
                    operator="+",
                    left=nodes.LiteralNode(2),
                    right=nodes.LiteralNode(2),
                ),
                right=nodes.LiteralNode(2),
            ),
        ),
        (
            "-2",
            nodes.UnaryExpressionNode(
                operator="-",
                value=nodes.LiteralNode(2),
            ),
        ),
        (
            "+2",
            nodes.UnaryExpressionNode(
                operator="+",
                value=nodes.LiteralNode(2),
            ),
        ),
        (
            "~1",
            nodes.UnaryExpressionNode(
                operator="~",
                value=nodes.LiteralNode(1),
            ),
        ),
        (
            "not 1",
            nodes.UnaryExpressionNode(
                operator="not",
                value=nodes.LiteralNode(1),
            ),
        ),
        (
            "-(2+2)",
            nodes.UnaryExpressionNode(
                operator="-",
                value=nodes.BinaryExpressionNode(
                    operator="+",
                    left=nodes.LiteralNode(2),
                    right=nodes.LiteralNode(2),
                ),
            ),
        ),
        (
            "1 > 2",
            nodes.BinaryExpressionNode(
                operator=">",
                left=nodes.LiteralNode(1),
                right=nodes.LiteralNode(2),
            ),
        ),
        (
            "1 > 2 > 3",
            nodes.AllOfNode(
                expressions=(
                    nodes.BinaryExpressionNode(
                        operator=">",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                    nodes.BinaryExpressionNode(
                        operator=">",
                        left=nodes.LiteralNode(2),
                        right=nodes.LiteralNode(3),
                    ),
                ),
            ),
        ),
        (
            "1 > 2 < 3",
            nodes.AllOfNode(
                expressions=(
                    nodes.BinaryExpressionNode(
                        operator=">",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                    nodes.BinaryExpressionNode(
                        operator="<",
                        left=nodes.LiteralNode(2),
                        right=nodes.LiteralNode(3),
                    ),
                ),
            ),
        ),
        (
            "1 > 2 or 1 < 2",
            nodes.AnyOfNode(
                expressions=(
                    nodes.BinaryExpressionNode(
                        operator=">",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                    nodes.BinaryExpressionNode(
                        operator="<",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                ),
            ),
        ),
        (
            "1 > 2 and 1 < 2",
            nodes.AllOfNode(
                expressions=(
                    nodes.BinaryExpressionNode(
                        operator=">",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                    nodes.BinaryExpressionNode(
                        operator="<",
                        left=nodes.LiteralNode(1),
                        right=nodes.LiteralNode(2),
                    ),
                ),
            ),
        ),
        (
            "2+2*2 > (2+2)*2",
            nodes.BinaryExpressionNode(
                operator=">",
                left=nodes.BinaryExpressionNode(
                    operator="+",
                    left=nodes.LiteralNode(2),
                    right=nodes.BinaryExpressionNode(
                        operator="*",
                        left=nodes.LiteralNode(2),
                        right=nodes.LiteralNode(2),
                    ),
                ),
                right=nodes.BinaryExpressionNode(
                    operator="*",
                    left=nodes.BinaryExpressionNode(
                        operator="+",
                        left=nodes.LiteralNode(2),
                        right=nodes.LiteralNode(2),
                    ),
                    right=nodes.LiteralNode(2),
                ),
            ),
        ),
    ],
)
def test_parse(
    expression: str,
    result: nodes.Node,
    parser: ExpressionEvalParser,
) -> None:
    assert parser.parse(expression) == result


def test_invalid_syntax(parser: ExpressionEvalParser) -> None:
    expression = "from 1"
    with pytest.raises(ExpressionInvalidError):
        parser.parse(expression)


def test_unknown_ast_node(parser: ExpressionEvalParser) -> None:
    expression = "function(1)"
    with pytest.raises(UnknownAstNodeError):
        parser.parse(expression)


@pytest.mark.parametrize(
    ("expression", "field_name"),
    [
        ("ctx.is_admin", "is_admin"),
        ("ctx.division_id", "division_id"),
    ],
)
def test_from_context_attribute(
    parser: ExpressionEvalParser,
    expression: str,
    field_name: str,
) -> None:
    assert parser.parse(expression) == nodes.FromContextNode(
        field_name=field_name,
    )


def test_from_context_attribute_custom_alias() -> None:
    parser = ExpressionEvalParser(
        [*get_builtin_handlers(), FromContextAttributeHandler(alias="user")],
    )
    assert parser.parse("user.age") == nodes.FromContextNode(field_name="age")


def test_from_context_attribute_requires_alias_prefix(
    parser: ExpressionEvalParser,
) -> None:
    with pytest.raises(UnknownAstNodeError):
        parser.parse("user.is_admin")
