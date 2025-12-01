import dataclasses
import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import median
from string import Template
from typing import Dict, Generator, List

from src.interfaces import BaseConfig
from src.parse_utils import parse_log
from src.utils import BaseToDict


def create_generator(path: Path) -> Generator[str, None, None]:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            for line in f:
                yield line.decode("utf-8")
    else:
        with open(path, "rb") as f:
            for line in f:
                yield line.decode("utf-8")


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


class App:
    def __init__(self, root: str, config: BaseConfig):
        self.config = config

        dir_log = Path(root, config["LOG_DIR"])
        dir_report = Path(root, config["REPORT_DIR"])

        if not dir_log.exists():
            raise FileNotFoundError(f"Log directory {dir_log} does not exist")

        if not dir_report.exists():
            dir_report.mkdir(parents=True, exist_ok=True)

        self.dir_log = dir_log
        self.dir_report = dir_report

        self.count_total: int = 0
        self.time_total: float = 0

        self.urls_statistics: Dict[str, UrlStat] = dict()

    def get_last_log_path(self) -> tuple[Path | None, datetime | None]:
        last_log_path = None
        last_log_date = None

        pattern = r"^nginx-access-ui\.log-(\d{8})(?:\.gz)?$"

        for file_path in self.dir_log.iterdir():
            if file_path.is_file():
                match = re.search(pattern, file_path.name)
                if not match:
                    continue

                date_str = match.group(1)

                date = datetime.strptime(date_str, "%Y%m%d")
                if last_log_date is None or date > last_log_date:  # type: ignore
                    last_log_date = date
                    last_log_path = file_path

        return last_log_path, last_log_date

    def save_report(self, log_date: datetime) -> None:
        with open("report.html") as templ:
            content = templ.read()

            template = Template(content)
            report_path = self.dir_report.joinpath(f"report_{log_date.strftime('%Y.%m.%d')}.html")

            with open(report_path, "w", encoding="utf-8") as out:
                out.write(
                    template.safe_substitute(
                        {"table_json": json.dumps(sorted([log_stat.to_dict() for log_stat in self.urls_statistics.values()], key=lambda x: x["time_sum"], reverse=True))}
                    )
                )

    def run(self) -> None:
        last_log_path, last_log_date = self.get_last_log_path()

        if last_log_path is None or last_log_date is None:
            return None

        generator = create_generator(last_log_path)

        for line in generator:
            log = parse_log(line)

            if log is None:
                print("error parsing log")
                continue

            if log.url not in self.urls_statistics:
                self.urls_statistics[log.url] = UrlStat(url=log.url)

            log_stat = self.urls_statistics[log.url]
            log_stat.count += 1
            log_stat.times.append(log.duration)
            self.count_total += 1
            self.time_total += log.duration

            # TODO: delete
            if self.count_total > 1000:
                break

        for log_stat in self.urls_statistics.values():
            log_stat.compute_values(self.count_total, self.time_total)

        self.save_report(last_log_date)
        return None
