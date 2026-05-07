from pathlib import Path

from app.session_check.activities import parse_sessions
from app.shared.models import Session

MOCK_HTML = (Path(__file__).parent.parent / "src/app/session_check/mocks/index.html").read_text()

WHITESPACE = "                                                                "


def test_returns_empty_dict_for_empty_html():
    assert parse_sessions("<html></html>") == {}


def test_returns_all_date_panes():
    result = parse_sessions(MOCK_HTML)
    assert "2026-05-07" in result
    assert "2026-05-12" in result


def test_returns_all_sessions_for_date():
    result = parse_sessions(MOCK_HTML)
    assert len(result["2026-05-07"]) == 28


def test_first_session_fields_for_date():
    result = parse_sessions(MOCK_HTML)
    first = result["2026-05-07"][0]
    assert first.name == "Power"
    assert first.instructor == "Анна Бутурліна"
    assert first.time.startswith("07:45")
    assert "08:40" in first.time


def test_returns_sessions_for_different_date():
    result = parse_sessions(MOCK_HTML)
    sessions = result["2026-05-12"]
    assert len(sessions) == 28
    assert sessions[0] == Session(
        name="Games",
        time=f"07:45{WHITESPACE}- 08:30{WHITESPACE}(45 хв{WHITESPACE})",
        instructor="Анна Бутурліна",
    )


def test_session_names_are_non_empty():
    result = parse_sessions(MOCK_HTML)
    assert all(s.name for s in result["2026-05-07"])


def test_session_instructors_are_non_empty():
    result = parse_sessions(MOCK_HTML)
    assert all(s.instructor for s in result["2026-05-07"])
