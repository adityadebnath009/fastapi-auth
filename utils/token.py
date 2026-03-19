import os
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from core.settings import settings

ALGORITHM = "HS256"

def create_access_token(data: dict):

    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload["type"] = "access"
    return jwt.encode(payload, settings.access_secret_key, algorithm=ALGORITHM)

def decode_email_token(token: str):
    try:
        payload = jwt.decode(token, settings.email_secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.access_secret_key,algorithms=[ALGORITHM])

        return payload
    except JWTError:
        return None

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.refresh_secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def create_refresh_token(data: dict):

    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.refresh_secret_key, algorithm=ALGORITHM)


