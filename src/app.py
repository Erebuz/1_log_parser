import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, Generator

import structlog

from src.interfaces import BaseConfig
from src.parse_utils import parse_log
from src.url_stat import UrlStat

logger = structlog.get_logger()


def create_generator(path: Path) -> Generator[str, None, None]:
    f = gzip.open(path, "rb") if path.suffix == ".gz" else open(path, "rb")

    with f:
        for line in f:
            yield line.decode("utf-8")


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

    def save_report(self, log_date: datetime, urls_statistics: Dict[str, UrlStat]) -> None:
        with open("report.html") as templ:
            content = templ.read()

            template = Template(content)
            report_path = self.get_report_path(log_date)

            with open(report_path, "w", encoding="utf-8") as out:
                out.write(
                    template.safe_substitute(
                        {"table_json": json.dumps(sorted([log_stat.to_dict() for log_stat in urls_statistics.values()], key=lambda x: x["time_sum"], reverse=True))}
                    )
                )

    def run(self) -> None:
        last_log_path, last_log_date = self.get_last_log_path()

        if last_log_path is None or last_log_date is None:
            logger.info("File not found", path=last_log_path)
            return None

        exist_report_path = self.check_report_exists(last_log_date)
        if exist_report_path is not None:
            logger.info("Report exists", path=exist_report_path)
            logger.info("Cancel parse file", path=last_log_path)
            return None

        logger.info("Start parse file", path=last_log_path)

        generator = create_generator(last_log_path)

        lines_counter = 0
        errors_counter = 0
        time_total: float = 0

        urls_statistics: Dict[str, UrlStat] = dict()

        for line in generator:
            lines_counter += 1

            try:
                log = parse_log(line)
            except ValueError:
                logger.error("Parse error", path=last_log_path, line=line)
                log = None

            if log is None:
                errors_counter += 1
                continue

            if log.url not in urls_statistics:
                urls_statistics[log.url] = UrlStat(url=log.url)

            log_stat = urls_statistics[log.url]
            log_stat.count += 1
            log_stat.times.append(log.duration)

            time_total += log.duration

        for log_stat in urls_statistics.values():
            lines_correct_total = lines_counter - errors_counter
            log_stat.compute_values(lines_correct_total, time_total)

        self.save_report(last_log_date, urls_statistics)

        self.check_error_limit(lines_counter, errors_counter)

        logger.info("End parse file", path=last_log_path)
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
