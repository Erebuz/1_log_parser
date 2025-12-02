import gzip
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator


class BaseToDict:
    @staticmethod
    def _to_dict(value: Any, deep: bool = False) -> Any:
        if isinstance(value, BaseToDict):
            return value.to_dict(deep=deep) if deep else None
        elif isinstance(value, datetime):
            return value.timestamp()
        elif isinstance(value, list):
            return [v.to_dict(deep=deep) if hasattr(v, "to_dict") else v for v in value] if deep else None
        elif isinstance(value, float):
            return round(value, 3)
        else:
            return value

    def to_dict(self, deep: bool = False) -> Dict[str, Any]:
        return {k: self._to_dict(v, deep) for k, v in self.__dict__.items() if not k.startswith("_")}


def create_generator(path: Path) -> Generator[str, None, None]:
    f = gzip.open(path, "rb") if path.suffix == ".gz" else open(path, "rb")

    with f:
        for line in f:
            yield line.decode("utf-8")
