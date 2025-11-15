"""
Database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """User model for authentication and profile"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class Conversation(Base):
    """Conversation/Thread model for chat sessions"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String, nullable=True)  # Optional conversation title
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversations")
    checkpoints = relationship("Checkpoint", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, thread_id='{self.thread_id}')>"


class Checkpoint(Base):
    """Checkpoint model for storing LangGraph state snapshots"""

    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("conversations.thread_id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint_id = Column(String, nullable=False)  # LangGraph checkpoint ID
    parent_checkpoint_id = Column(String, nullable=True)  # Parent checkpoint for branching
    checkpoint_data = Column(Text, nullable=False)  # JSON serialized checkpoint data
    checkpoint_metadata = Column(Text, nullable=True)  # JSON serialized metadata (renamed to avoid SQLAlchemy reserved word)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="checkpoints")

    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_thread_checkpoint', 'thread_id', 'checkpoint_id'),
    )

    def __repr__(self):
        return f"<Checkpoint(id={self.id}, thread_id='{self.thread_id}', checkpoint_id='{self.checkpoint_id}')>"
