from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.raises import RaisesExc

from src.parse_utils import Log, parse_log

valid = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
no_date = '1.196.116.32 -   "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
bad_date = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +00] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
bad_url = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'


@pytest.mark.parametrize(
    "line, expectation, expected",
    [
        (
            "",
            pytest.raises(AttributeError),
            None,
        ),
        (
            valid,
            does_not_raise(),
            Log,
        ),
        (
            no_date,
            pytest.raises(AttributeError),
            None,
        ),
        (
            bad_date,
            pytest.raises(ValueError),
            None,
        ),
        (
            bad_url,
            pytest.raises(AttributeError),
            None,
        ),
    ],
    ids=["empty", "valid", "no-date", "bad-tz", "bad-reqline"],
)
def test_parse_log(line: str, expectation: does_not_raise[None] | RaisesExc[ValueError], expected: type[Log] | None) -> None:
    with expectation:
        result = parse_log(line)
        if expected is None:
            assert result is None
        else:
            assert isinstance(result, expected)
