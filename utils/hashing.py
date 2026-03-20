from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"])


def hash_password(password: str):
    return pwd_context.hash(password)


from passlib.exc import UnknownHashError

def verify_password(password: str, hashed_password: str):
    try:
        return pwd_context.verify(password, hashed_password)
    except UnknownHashError:
        # Gracefully handle legacy or malformed hashes in the database
        return False

