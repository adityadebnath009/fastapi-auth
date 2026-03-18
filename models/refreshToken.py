

from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, String

from database.connection import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String(512), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable = False )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)