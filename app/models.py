from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class User(Base): #for signup and login info
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code_snippet = Column(Text, nullable=False)
    findings = Column(JSON)
    source = Column(String, default="manual", nullable=False)
    repo_full_name = Column(String, nullable=True)
    pr_number = Column(Integer, nullable=True)
    pr_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    warnings = Column(JSON, nullable=True)
    head_sha = Column(String, nullable=True)
