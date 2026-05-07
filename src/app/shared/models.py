from dataclasses import dataclass


@dataclass
class Session:
    name: str
    time: str
    instructor: str


@dataclass
class NotificationState:
    last_notified: str
    notified_at: str
