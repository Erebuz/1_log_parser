from typing import TypedDict


class BaseConfig(TypedDict):
    LOG_DIR: str
    REPORT_DIR: str
    PARSE_LOG_PATH: str | None
    ERROR_LIMIT: int | None
