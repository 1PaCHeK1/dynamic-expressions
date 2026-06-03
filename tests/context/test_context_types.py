from typing import assert_type

from dynamic_expressions.context import Context, Expression, Mapped, mapped_field


class UserContext(Context):
    grade_level: int
    is_admin: Mapped[bool] = mapped_field(default=False)
    division_id: Mapped[int] = mapped_field(default=1)


def test_context_dsl_static_types() -> None:
    user = UserContext(grade_level=1)
    assert_type(UserContext.is_admin, Expression[bool])
    assert_type(UserContext.division_id, Expression[int])
    assert_type(user.is_admin, bool)
    assert_type(user.division_id, int)
    assert_type(user.grade_level, int)
