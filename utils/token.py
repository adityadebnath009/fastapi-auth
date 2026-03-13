import os
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
print("SECRET KEY:", SECRET_KEY)

ALGORITHM = "HS256"

def create_access_token(data: dict):

    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=30)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])

        return payload
    except JWTError as e:
        print("JWT ERROR:", e)
        return None

def create_refresh_token(data: dict):

    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
