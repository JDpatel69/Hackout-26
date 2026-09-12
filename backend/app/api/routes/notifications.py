from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import RoleAny
from app.database import get_db
from app.models import AppNotification, User
from app.schemas import MessageOut, NotificationOut
from app.utils.mappers import notification_out

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    user: User = Depends(RoleAny),
    db: Session = Depends(get_db),
) -> List[NotificationOut]:
    rows = (
        db.query(AppNotification)
        .filter(AppNotification.user_id == user.id)
        .order_by(AppNotification.created_at.desc())
        .all()
    )
    return [notification_out(n) for n in rows]


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str,
    user: User = Depends(RoleAny),
    db: Session = Depends(get_db),
) -> NotificationOut:
    n = db.get(AppNotification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return notification_out(n)


@router.post("/read-all", response_model=MessageOut)
def mark_all_read(
    user: User = Depends(RoleAny),
    db: Session = Depends(get_db),
) -> MessageOut:
    db.query(AppNotification).filter(
        AppNotification.user_id == user.id,
        AppNotification.is_read.is_(False),
    ).update({"is_read": True})
    db.commit()
    return MessageOut(message="All notifications marked as read")
