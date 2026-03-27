from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from models.refreshToken import RefreshToken

from models.user_model import User
from models.email_verification_model import EmailVerificationToken
from utils.hashing import hash_password


# Repositories ---> Takes the data and talk to Database

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
    hashed_token = hash_password(token)

    refresh_token = RefreshToken(
        token=hashed_token,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def revoke_refresh_token(db: Session, refreshToken: RefreshToken):
    refreshToken.revoked = True
    db.commit()
    db.refresh(refreshToken)



def get_active_refresh_tokens_for_user(db: Session, user_id: int):
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
        .all()
    )


def save_verification_token_to_db(db, user_id: int, token: str):
    """
    Store verification token in DB for tracking/invalidation
    (Hybrid approach: JWT carries expiry, DB tracks usage)
    """


    # Calculate expiry (24 hours from now)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    # Store hashed token for security
    hashed_token = hash_password(token)

    db_token = EmailVerificationToken(
        token=hashed_token,
        user_id=user_id,
        expires_at=expires_at,
        used=False
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token
