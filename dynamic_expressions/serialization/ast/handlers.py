import ast
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from dynamic_expressions import nodes
from dynamic_expressions.types import BinaryExpressionOperator

OPERATOR_MAPPING: Mapping[
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


def _map_op(node: ast.operator | ast.cmpop) -> BinaryExpressionOperator:
    operator = OPERATOR_MAPPING.get(type(node))
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


class BinaryHandler(
    ExpressionHandler[ast.BinOp, nodes.BinaryExpressionNode],
):
    def satisfy(self, ast_: ast.AST) -> bool:
        return isinstance(ast_, ast.BinOp)

    def map(self, ast_: ast.BinOp, dispatch: Dispatch) -> nodes.BinaryExpressionNode:
        return nodes.BinaryExpressionNode(
            operator=_map_op(ast_.op),
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
                operator=_map_op(op),
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


def get_builtin_handlers() -> Sequence[ExpressionHandler[Any, Any]]:
    return [
        ConstantHandler(),
        BinaryHandler(),
        CompareHandler(),
        AnyOfHandler(),
        AllOfHandler(),
    ]
