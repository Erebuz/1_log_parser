import dataclasses
from statistics import median
from typing import List

from src.utils import BaseToDict


@dataclasses.dataclass
class UrlStat(BaseToDict):
    url: str
    count: int = 0
    count_perc: float = 0
    _times: List[float] = dataclasses.field(default_factory=list)
    time_sum: float = 0
    time_perc: float = 0
    time_avg: float = 0
    time_max: float = 0
    _time_min: float = 0
    time_med: float = 0

    def compute_values(self, count_total: int, time_total: float) -> None:
        self.time_sum = sum(self._times)
        self.time_avg = sum(self._times) / len(self._times)
        self.time_max = max(self._times)
        self._time_min = min(self._times)
        self.time_med = median(self._times)

        self.count_perc = self.count / count_total * 100
        self.time_perc = self.time_sum / time_total * 100

    @property
    def times(self) -> List[float]:
        return self._times
