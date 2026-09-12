"""Notification helper."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AppNotification
from app.utils.ids import new_id, now


def notify(
    db: Session,
    user_id: str,
    type_: str,
    title: str,
    message: str,
    link_to: str | None = None,
) -> AppNotification:
    n = AppNotification(
        id=new_id(),
        user_id=user_id,
        type=type_,
        title=title,
        message=message,
        is_read=False,
        created_at=now(),
        link_to=link_to,
    )
    db.add(n)
    return n
