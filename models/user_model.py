from sqlalchemy import Column, Integer, String

from database.connection import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True, nullable=False)

    password = Column(String(255), nullable=True)

    provider = Column(String(50), nullable=False, default="local")

    provider_id = Column(String(255), nullable=True)



