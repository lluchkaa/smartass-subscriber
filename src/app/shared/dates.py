from datetime import date, timedelta


def target_week(from_date: date) -> list[date]:
    """Returns SAT–FRI of the week two Mondays ahead of from_date."""
    days_to_next_monday = (7 - from_date.weekday()) % 7 or 7
    monday = from_date + timedelta(days=days_to_next_monday + 7)
    return [monday + timedelta(days=d) for d in range(-2, 5)]
