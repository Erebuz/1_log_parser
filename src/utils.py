from datetime import datetime
from typing import Any, Dict


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
