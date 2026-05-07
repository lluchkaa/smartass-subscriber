from datetime import date, timedelta


def target_monday(from_date: date) -> date:
    """Returns the Monday one week after the next Monday from from_date."""
    days_to_next_monday = (7 - from_date.weekday()) % 7 or 7
    return from_date + timedelta(days=days_to_next_monday + 7)
