import ast
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from dynamic_expressions import nodes
from dynamic_expressions.types import BinaryExpressionOperator, UnaryExpressionOperator

UNARY_OPERATOR_MAPPING: Mapping[
    type[ast.unaryop],
    UnaryExpressionOperator,
] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Invert: "~",
    ast.Not: "not",
}


BINARY_OPERATOR_MAPPING: Mapping[
    type[ast.operator | ast.cmpop],
    BinaryExpressionOperator,
] = {
    ast.Eq: "=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.NotEq: "!=",
    ast.In: "in",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Pow: "^",
    ast.BitAnd: "&",
    ast.BitOr: "|",
}


def _map_unary_op(node: ast.unaryop) -> UnaryExpressionOperator:
    operator = UNARY_OPERATOR_MAPPING.get(type(node))
    if operator is None:
        msg = f"Unknown operator '{node.__class__.__qualname__}'"
        raise ValueError(msg)
    return operator


def _map_binary_op(node: ast.operator | ast.cmpop) -> BinaryExpressionOperator:
    operator = BINARY_OPERATOR_MAPPING.get(type(node))
    if operator is None:
        msg = f"Unknown operator '{node.__class__.__qualname__}'"
        raise ValueError(msg)
    return operator


class Dispatch(Protocol):
    def __call__(self, node: ast.AST) -> nodes.Node: ...


class ExpressionHandler[TAst: ast.AST, TNode: nodes.Node](Protocol):
    def satisfy(self, ast_: ast.AST) -> bool: ...
    def map(self, ast_: TAst, dispatch: Dispatch) -> TNode: ...


class ConstantHandler(
    ExpressionHandler[
        ast.Constant | ast.Tuple | ast.List,
        nodes.LiteralNode,
    ],
):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, (ast.Constant, ast.Tuple, ast.List))

    def map(
        self, ast_: ast.Constant | ast.Tuple | ast.List, dispatch: Dispatch
    ) -> nodes.LiteralNode:
        if isinstance(ast_, (ast.Tuple, ast.List)):
            return nodes.LiteralNode(
                value=tuple(dispatch(v) for v in ast_.elts),
            )
        return nodes.LiteralNode(ast_.value)


class UnaryHandler(ExpressionHandler[ast.UnaryOp, nodes.UnaryExpressionNode]):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.UnaryOp)

    def map(self, ast_: ast.UnaryOp, dispatch: Dispatch) -> nodes.UnaryExpressionNode:
        return nodes.UnaryExpressionNode(
            operator=_map_unary_op(ast_.op),
            value=dispatch(ast_.operand),
        )


class BinaryHandler(
    ExpressionHandler[ast.BinOp, nodes.BinaryExpressionNode],
):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.BinOp)

    def map(self, ast_: ast.BinOp, dispatch: Dispatch) -> nodes.BinaryExpressionNode:
        return nodes.BinaryExpressionNode(
            operator=_map_binary_op(ast_.op),
            left=dispatch(ast_.left),
            right=dispatch(ast_.right),
        )


class CompareHandler(
    ExpressionHandler[ast.Compare, nodes.AllOfNode | nodes.BinaryExpressionNode]
):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.Compare)

    def map(
        self, ast_: ast.Compare, dispatch: Dispatch
    ) -> nodes.AllOfNode | nodes.BinaryExpressionNode:
        left = dispatch(ast_.left)
        expressions = tuple(
            nodes.BinaryExpressionNode(
                operator=_map_binary_op(op),
                left=left,
                right=(left := dispatch(right)),
            )
            for op, right in zip(
                ast_.ops,
                ast_.comparators,
                strict=True,
            )
        )
        if len(expressions) == 1:
            return expressions[0]
        return nodes.AllOfNode(expressions=expressions)


class AnyOfHandler(ExpressionHandler[ast.BoolOp, nodes.AnyOfNode]):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.BoolOp) and isinstance(ast_.op, ast.Or)

    def map(self, ast_: ast.BoolOp, dispatch: Dispatch) -> nodes.AnyOfNode:
        return nodes.AnyOfNode(expressions=tuple(dispatch(i) for i in ast_.values))


class AllOfHandler(ExpressionHandler[ast.BoolOp, nodes.AllOfNode]):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.BoolOp) and isinstance(ast_.op, ast.And)

    def map(self, ast_: ast.BoolOp, dispatch: Dispatch) -> nodes.AllOfNode:
        return nodes.AllOfNode(expressions=tuple(dispatch(i) for i in ast_.values))


class FromContextAttributeHandler(
    ExpressionHandler[ast.Attribute, nodes.FromContextNode]
):
    def __init__(self, alias: str = "ctx") -> None:
        self._alias = alias

    def satisfy(self, ast_: ast.AST) -> bool:
        return (
            isinstance(ast_, ast.Attribute)
            and isinstance(ast_.value, ast.Name)
            and ast_.value.id == self._alias
        )

    def map(self, ast_: ast.Attribute, dispatch: Dispatch) -> nodes.FromContextNode:  # noqa: ARG002
        return nodes.FromContextNode(field_name=ast_.attr)


def get_builtin_handlers() -> Sequence[ExpressionHandler[Any, Any]]:
    return [
        ConstantHandler(),
        UnaryHandler(),
        BinaryHandler(),
        CompareHandler(),
        AnyOfHandler(),
        AllOfHandler(),
    ]
