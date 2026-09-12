from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import User
from app.schemas import AuthSessionOut, MessageOut, SignInRequest, UserOut
from app.utils.ids import now
from app.utils.mappers import user_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signin", response_model=AuthSessionOut)
def sign_in(body: SignInRequest, db: Session = Depends(get_db)) -> AuthSessionOut:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.last_login_at = now()
    db.commit()
    token, expires = create_access_token(user.id, user.role)
    return AuthSessionOut(user=user_out(user), token=token, expiresAt=expires)


@router.post("/signout", response_model=MessageOut)
def sign_out(_: User = Depends(get_current_user)) -> MessageOut:
    # Stateless JWT — client discards token. Endpoint exists for frontend parity.
    return MessageOut(message="Signed out")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)


@router.post("/refresh", response_model=AuthSessionOut)
def refresh(user: User = Depends(get_current_user)) -> AuthSessionOut:
    token, expires = create_access_token(user.id, user.role)
    return AuthSessionOut(user=user_out(user), token=token, expiresAt=expires)
