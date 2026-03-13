from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from models.refreshToken import RefreshToken

from models.user_model import User


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str):
    user = User(email=email, password=password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def save_refresh_token(db: Session, user_id: int, token: str):
    refresh_token = RefreshToken(
        token = token,
        user_id = user_id,
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    )

    db.add(refresh_token)
    db.commit()
    return refresh_token

def get_refresh_token(db: Session,  token: str):
    return db.query(RefreshToken).filter(RefreshToken.token==token).first()

def revoke_refresh_token(db: Session, token: str):
    token = get_refresh_token(db, token)
    if token:
        RefreshToken.token = True
        db.commit()


