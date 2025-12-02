from datetime import datetime, timezone

import pytest

from src.utils import BaseToDict


class Child(BaseToDict):
    def __init__(self, x: int) -> None:
        self.x = x


class Sample(BaseToDict):
    def __init__(self) -> None:
        self.s = "str"
        self.f = 1.23456
        self.d = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.child = Child(5)
        self.items = [Child(1), Child(2)]
        self._hidden = "secret"


def test_to_dict_shallow() -> None:
    obj = Sample()
    data = obj.to_dict(deep=False)
    assert data["s"] == "str"
    assert data["f"] == pytest.approx(1.235)
    assert isinstance(data["d"], float)
    assert data["child"] is None
    assert data["items"] is None
    assert "_hidden" not in data


def test_to_dict_deep() -> None:
    obj = Sample()
    data = obj.to_dict(deep=True)
    assert data["child"] == {"x": 5}
    assert data["items"] == [{"x": 1}, {"x": 2}]
