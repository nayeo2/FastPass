from sqlalchemy import Column, BigInteger, String, DateTime, func
from app.db import Base

class TicketRequest(Base):
    __tablename__ = "ticket_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    event_id = Column(BigInteger, nullable=False)
    seat_id = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="QUEUED")
    error_message = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())