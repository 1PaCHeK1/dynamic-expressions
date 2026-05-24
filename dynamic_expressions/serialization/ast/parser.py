import ast
from collections.abc import Sequence
from dataclasses import dataclass

from dynamic_expressions.nodes import Node
from dynamic_expressions.serialization.ast.handlers import ExpressionHandler


class ExpressionInvalidError(Exception): ...


@dataclass
class UnknownAstNodeError(Exception):
    node: str


class ExpressionEvalParser:
    def __init__(self, handlers: Sequence[ExpressionHandler[ast.AST, Node]]) -> None:
        self._handlers = handlers

    def parse(self, expression: str) -> Node | None:
        if not expression:
            return None

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise ExpressionInvalidError from e
        return self._visit(self._unwrap_tree(tree))

    def _visit(self, node: ast.AST) -> Node:
        node_ = next(
            (
                handler.map(node, dispatch=self._visit)
                for handler in self._handlers
                if handler.satisfy(node)
            ),
            None,
        )
        if node_ is None:
            raise UnknownAstNodeError(ast.dump(node))
        return node_

    def _unwrap_tree(self, tree: ast.AST) -> ast.AST:
        if isinstance(tree, ast.Expression):
            return tree.body
        return tree
