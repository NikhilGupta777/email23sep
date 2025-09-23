from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")  # 'admin' or 'user'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, index=True)  # Changed to String to match existing database
    # Temporarily remove user_id to avoid database column issues
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    template_id = Column(String, ForeignKey("templates.id"))  # Changed to String to match templates.id
    sender_email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  # 'draft', 'sending', 'completed', 'failed'

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Add user_id for individual emails
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    recipient_email = Column(String)
    status = Column(String, default="sent")  # 'sent', 'failed', 'bounced'
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)