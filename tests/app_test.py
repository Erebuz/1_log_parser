from datetime import datetime
from pathlib import Path

from src.app import App
from src.url_stat import UrlStat


def make_app(tmp_path: Path) -> App:
    logs = tmp_path / "logs"
    reports = tmp_path / "reports"
    logs.mkdir()
    reports.mkdir()
    config = {
        "LOG_DIR": "logs",
        "REPORT_DIR": "reports",
        "PARSE_LOG_PATH": None,
        "ERROR_LIMIT": None,
    }
    return App(str(tmp_path), config)  # type: ignore[arg-type]


def test_get_last_log_path(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    (tmp_path / "logs" / "nginx-access-ui.log-20240101.gz").write_text("")
    (tmp_path / "logs" / "nginx-access-ui.log-20250101").write_text("")
    path, date = app.get_last_log_path()
    assert path is not None and "20250101" in path.name
    assert date == datetime(2025, 1, 1)


def test_get_report_path(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    d = datetime(2025, 7, 30)
    p = app.get_report_path(d)
    assert p == tmp_path / "reports" / "report_2025.07.30.html"


def test_check_report_exists(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    d = datetime(2025, 7, 30)
    p = app.get_report_path(d)
    p.write_text("")
    assert app.check_report_exists(d) == p
    p.unlink()
    assert app.check_report_exists(d) is None


def test_save_report(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    stats = {"/": UrlStat(url="/")}
    d = datetime(2025, 7, 30)
    app.save_report(d, stats)
    out = app.get_report_path(d)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "var table = [" in content


def test_run_creates_report(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    log_line = (
        '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" '
        '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" '
        '"dc7161be3" 0.390\n'
    )
    (tmp_path / "logs" / "nginx-access-ui.log-20170630").write_text(log_line)
    app.run()
    out = tmp_path / "reports" / "report_2017.06.30.html"
    assert out.exists()
