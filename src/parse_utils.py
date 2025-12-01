import dataclasses
import re
from datetime import datetime

LOG_PATTERN = re.compile(
    r"(?P<ip>[\d\.]+)\s+"  # IP адрес
    r"(?P<identd>\S+)\s+"  # identd
    r"(?P<user>\S+)\s+"  # user
    r"\[(?P<date>.*?)\]\s+"  # время в квадратных скобках
    r'"(?P<request>.*?)"\s+'  # строка запроса в кавычках
    r"(?P<status>\d+)\s+"  # статус код
    r"(?P<bytesize>\S+)\s+"  # байты
    r'"(?P<referer>.*?)"\s+'  # referer
    r'"(?P<user_agent>.*?)"\s+'  # user agent
    r'"(?P<forwarded_for>.*?)"\s+'  #
    r'"(?P<req_id>.*?)"\s+'  # ID запроса
    r'"(?P<sess_id>.*?)"\s+'  # ID сессии
    r"(?P<duration>[\d\.]+)"  # время выполнения
)


@dataclasses.dataclass
class Log:
    ip: str
    identd: str
    user: str
    date: datetime
    request: str
    method: str | None
    url: str
    protocol: str | None
    status: int
    bytesize: int
    referer: str
    user_agent: str
    forwarded_for: str
    req_id: str
    sess_id: str
    duration: float

    def __init__(self, **kwargs: str) -> None:
        for k, v in kwargs.items():
            if k == "request":
                req_parts = v.split()
                try:
                    method, url, protocol = req_parts
                except ValueError:
                    method, protocol = (None, None)
                    url = v

                self.method = method
                self.url = url
                self.protocol = protocol
                continue

            val: str | int | float | datetime | None

            if k == "status":
                val = int(v)
            elif k == "bytesize":
                val = int(v)
            elif k == "duration":
                val = float(v)
            elif k == "date":
                try:
                    val = datetime.strptime(v, "%d/%b/%Y:%H:%M:%S %z")
                except ValueError:
                    val = None
            else:
                val = v

            setattr(self, k, val)


def parse_log(line: str) -> Log | None:
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    match_data = match.groupdict()

    data = Log(**match_data)

    return data
