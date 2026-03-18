import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.settings import settings
load_dotenv()
DATABASE_URL  = os.getenv("DATABASE_URL")

engine = create_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    echo=settings.app_env == "development"
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()