import pytest
import re
from typing import Any, Optional

from snuba_sdk.entity import Entity
from snuba_sdk.expressions import InvalidExpression
from snuba_sdk.relationships import Join, Relationship
from snuba_sdk.visitors import Translation


TRANSLATOR = Translation(use_entity_aliases=True)

relationship_tests = [
    pytest.param(
        Entity("events", "ev", 100),
        "contains",
        Entity("transactions", "t"),
        "(ev: events SAMPLE 100) -[contains]-> (t: transactions)",
        None,
    ),
    pytest.param(
        "",
        "contains",
        Entity("transactions", "t"),
        None,
        InvalidExpression("'' must be an Entity"),
    ),
    pytest.param(
        Entity("events", None, 100),
        "contains",
        Entity("transactions", "t"),
        None,
        InvalidExpression(
            "Entity(name='events', alias=None, sample=100) must have a valid alias"
        ),
    ),
    pytest.param(
        Entity("events", "ev", 100),
        1,
        Entity("transactions", "t"),
        None,
        InvalidExpression("'1' is not a valid relationship name"),
    ),
    pytest.param(
        Entity("events", "e", 100),
        "",
        Entity("transactions", "t"),
        None,
        InvalidExpression("'' is not a valid relationship name"),
    ),
]


@pytest.mark.parametrize("lhs, name, rhs, formatted, exception", relationship_tests)
def test_relationships(
    lhs: Any,
    name: Any,
    rhs: Any,
    formatted: Optional[str],
    exception: Optional[Exception],
) -> None:
    if exception is not None:
        with pytest.raises(type(exception), match=re.escape(str(exception))):
            Relationship(lhs, name, rhs)
    else:
        rel = Relationship(lhs, name, rhs)
        assert rel.lhs == lhs
        assert rel.name == name
        assert rel.rhs == rhs
        if formatted is not None:
            assert TRANSLATOR.visit(rel) == formatted


join_tests = [
    pytest.param(
        [Relationship(Entity("events", "e"), "has", Entity("sessions", "s"))],
        "(e: events) -[has]-> (s: sessions)",
        None,
    ),
    pytest.param(
        [
            Relationship(Entity("events", "e"), "has", Entity("sessions", "s")),
            Relationship(Entity("events", "e"), "hasnt", Entity("sessions", "s", 10)),
            Relationship(Entity("events", "e"), "musnt", Entity("sessions", "s")),
        ],
        "(e: events) -[has]-> (s: sessions), (e: events) -[hasnt]-> (s: sessions SAMPLE 10), (e: events) -[musnt]-> (s: sessions)",
        None,
    ),
    pytest.param(
        [], None, InvalidExpression("Join must have at least one Relationship")
    ),
    pytest.param(
        [1, 2], None, InvalidExpression("Join expects a list of Relationship objects")
    ),
    pytest.param(
        [
            Relationship(Entity("events", "e"), "has", Entity("sessions", "s")),
            Relationship(Entity("events", "e"), "hasnt", Entity("sessions", "e", 10)),
        ],
        None,
        InvalidExpression("alias 'e' is duplicated for entities events, sessions"),
    ),
]


@pytest.mark.parametrize("rels, formatted, exception", join_tests)
def test_joins(
    rels: Any,
    formatted: Optional[str],
    exception: Optional[Exception],
) -> None:
    if exception is not None:
        with pytest.raises(type(exception), match=re.escape(str(exception))):
            Join(rels)
    else:
        join = Join(rels)
        if formatted is not None:
            assert TRANSLATOR.visit(join) == formatted
