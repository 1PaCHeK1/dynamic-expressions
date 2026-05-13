import pytest
from dynamic_expressions import nodes
from dynamic_expressions.serialization.ast import (
    ExpressionEvalParser,
    get_builtin_handlers,
)
from dynamic_expressions.serialization.ast.parser import (
    ExpressionInvalidError,
    UnknownAstNodeError,
)


@pytest.fixture
def parser() -> ExpressionEvalParser:
    return ExpressionEvalParser(get_builtin_handlers())


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
