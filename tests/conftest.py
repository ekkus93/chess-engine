from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def record_xml_attribute() -> Callable[[str, object], None]:
    """Provide a stable no-op xml attribute recorder for local test runs.

    Some globally installed plugins request the experimental pytest fixture of the
    same name. Defining this local fixture avoids the experimental API warning
    without suppressing warnings globally.
    """

    def _record(_name: str, _value: object) -> None:
        return None

    return _record
