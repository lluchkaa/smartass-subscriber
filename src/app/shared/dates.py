from datetime import date, timedelta

DATE_FORMAT = "%Y-%m-%d"


def format_date(d: date) -> str:
    return d.strftime(DATE_FORMAT)


def target_week(from_date: date | None = None) -> list[date]:
    """Returns SAT–FRI of the week two Mondays ahead of from_date."""
    if from_date is None:
        from_date = date.today()
    days_to_next_monday = (7 - from_date.weekday()) % 7 or 7
    monday = from_date + timedelta(days=days_to_next_monday + 7)
    return [monday + timedelta(days=d) for d in range(-2, 5)]
