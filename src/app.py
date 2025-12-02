import dataclasses
import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import median
from string import Template
from typing import Dict, Generator, List

import structlog

from src.interfaces import BaseConfig
from src.parse_utils import parse_log
from src.utils import BaseToDict

logger = structlog.get_logger()


def create_generator(path: Path) -> Generator[str, None, None]:
    f = gzip.open(path, "rb") if path.suffix == ".gz" else open(path, "rb")

    with f:
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

        dir_log = Path(root, config.get("LOG_DIR", "logs"))
        dir_report = Path(root, config.get("REPORT_DIR", "reports"))

        if not dir_log.exists():
            raise FileNotFoundError(f"Log directory {dir_log} does not exist")

        if not dir_report.exists():
            dir_report.mkdir(parents=True, exist_ok=True)

        self.dir_log = dir_log
        self.dir_report = dir_report

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

    def get_report_path(self, log_date: datetime) -> Path:
        return self.dir_report.joinpath(f"report_{log_date.strftime('%Y.%m.%d')}.html")

    def check_report_exists(self, log_date: datetime) -> Path | None:
        report_path = self.get_report_path(log_date)
        if report_path.exists():
            return report_path
        else:
            return None

    def save_report(self, log_date: datetime) -> None:
        with open("report.html") as templ:
            content = templ.read()

            template = Template(content)
            report_path = self.get_report_path(log_date)

            with open(report_path, "w", encoding="utf-8") as out:
                out.write(
                    template.safe_substitute(
                        {"table_json": json.dumps(sorted([log_stat.to_dict() for log_stat in self.urls_statistics.values()], key=lambda x: x["time_sum"], reverse=True))}
                    )
                )

    def run(self) -> None:
        last_log_path, last_log_date = self.get_last_log_path()

        if last_log_path is None or last_log_date is None:
            logger.info("File not found", log_path=last_log_path)
            return None

        exist_report_path = self.check_report_exists(last_log_date)
        if exist_report_path is not None:
            logger.info("Report exists", report_path=exist_report_path)
            return None

        logger.info("Start parse file", log_path=last_log_path)

        generator = create_generator(last_log_path)

        lines_counter = 0
        errors_counter = 0
        time_total: float = 0

        for line in generator:
            lines_counter += 1

            try:
                log = parse_log(line)
            except ValueError:
                logger.error("Parse error", log_path=last_log_path, line=line)
                log = None

            if log is None:
                errors_counter += 1
                continue

            if log.url not in self.urls_statistics:
                self.urls_statistics[log.url] = UrlStat(url=log.url)

            log_stat = self.urls_statistics[log.url]
            log_stat.count += 1
            log_stat.times.append(log.duration)

            time_total += log.duration

            # TODO: delete
            if lines_counter - errors_counter >= 1000:
                break

        for log_stat in self.urls_statistics.values():
            lines_correct_total = lines_counter - errors_counter
            log_stat.compute_values(lines_correct_total, time_total)

        self.save_report(last_log_date)

        self.check_error_limit(lines_counter, errors_counter)
        return None

    def check_error_limit(self, lines: int, errors: int) -> None:
        error_percent = round(errors / lines * 100, 2) if lines > 0 else 0

        limit = self.config.get("ERROR_LIMIT", None)

        if limit is not None and error_percent > limit:
            logger.info(
                "The error limit has been exceeded",
                number_of_errors=errors,
                number_of_line=lines,
                percentage_of_errors=round(errors / lines * 100, 2) if lines > 0 else 0,
            )
