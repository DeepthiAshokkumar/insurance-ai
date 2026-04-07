from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .database import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(String) # 'approved' or 'rejected'
    extracted_details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
