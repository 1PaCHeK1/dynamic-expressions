from typing import Any

import pytest
from dynamic_expressions.serialization.pydantic import (
    BUILTIN_SCHEMAS,
    AllOfNodeSchema,
    AnyOfNodeSchema,
    FromContextNodeSchema,
    LiteralNodeSchema,
    PydanticExpressionParser,
    UnaryExpressionNodeSchema,
)


@pytest.fixture
def parser() -> PydanticExpressionParser:
    return PydanticExpressionParser(types=BUILTIN_SCHEMAS)


def test_parse(parser: PydanticExpressionParser) -> None:
    value = """{
  "type": "all-of",
  "expressions": [
    {
      "type": "any-of",
      "expressions": [
        {
          "type": "literal",
          "value": true
        }
      ]
    },
    {
      "type": "literal",
      "value": true
    }
  ]
}
    """
    result = parser.type_adapter.validate_json(value)
    assert result == AllOfNodeSchema[Any](
        type="all-of",
        expressions=(
            AnyOfNodeSchema(
                type="any-of",
                expressions=(LiteralNodeSchema(type="literal", value=True),),
            ),
            LiteralNodeSchema(type="literal", value=True),
        ),
    )


def test_dump(parser: PydanticExpressionParser) -> None:
    node = AllOfNodeSchema[Any](
        type="all-of",
        expressions=(
            AnyOfNodeSchema(
                type="any-of",
                expressions=(LiteralNodeSchema(type="literal", value=True),),
            ),
            LiteralNodeSchema(type="literal", value=True),
        ),
    )
    result = parser.type_adapter.dump_python(
        node,
        mode="json",
        warnings="none",
    )

    assert result == {
        "type": "all-of",
        "expressions": [
            {
                "type": "any-of",
                "expressions": [
                    {
                        "type": "literal",
                        "value": True,
                    },
                ],
            },
            {
                "type": "literal",
                "value": True,
            },
        ],
    }


def test_parse_unary(parser: PydanticExpressionParser) -> None:
    value = """{
  "type": "unary",
  "operator": "-",
  "value": {
    "type": "literal",
    "value": 1
  }
}
    """
    result = parser.type_adapter.validate_json(value)
    assert result == UnaryExpressionNodeSchema[Any](
        type="unary",
        operator="-",
        value=LiteralNodeSchema(type="literal", value=1),
    )


def test_dump_unary(parser: PydanticExpressionParser) -> None:
    node = UnaryExpressionNodeSchema[Any](
        type="unary",
        operator="-",
        value=LiteralNodeSchema(type="literal", value=1),
    )
    result = parser.type_adapter.dump_python(
        node,
        mode="json",
        warnings="none",
    )
    assert result == {
        "type": "unary",
        "operator": "-",
        "value": {
            "type": "literal",
            "value": 1,
        },
    }


def test_parse_from_context(parser: PydanticExpressionParser) -> None:
    value = """{
  "type": "from-context",
  "field_name": "user.name"
}
    """
    result = parser.type_adapter.validate_json(value)
    assert result == FromContextNodeSchema[Any](
        type="from-context",
        field_name="user.name",
    )


def test_dump_from_context(parser: PydanticExpressionParser) -> None:
    node = FromContextNodeSchema[Any](
        type="from-context",
        field_name="user.name",
    )
    result = parser.type_adapter.dump_python(
        node,
        mode="json",
        warnings="none",
    )
    assert result == {
        "type": "from-context",
        "field_name": "user.name",
    }
