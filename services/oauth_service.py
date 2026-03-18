from sqlalchemy.orm import Session
from models.user_model import User


def get_user_by_provider(db: Session, provider: str, provider_id: str):
    return db.query(User).filter(User.provider == provider,User.provider_id == provider_id
    ).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def find_or_create_oauth_user(db: Session, email: str, provider: str, provider_id: str) -> User:
    """
    Lookup priority:
    1. Match by provider + provider_id  (returning OAuth user)
    2. Match by email                   (user registered locally with same email → link account)
    3. Create new user
    """
    # 1. Exact provider match
    user = get_user_by_provider(db, provider, provider_id)
    if user:
        return user

    # 2. Email already exists (local account) → link the OAuth provider to it
    user = get_user_by_email(db, email)
    if user:
        user.provider = provider
        user.provider_id = provider_id
        db.commit()
        db.refresh(user)
        return user

    # 3. Brand new user
    user = User(
        email=email,
        password=None,       # OAuth users have no password
        provider=provider,
        provider_id=provider_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user