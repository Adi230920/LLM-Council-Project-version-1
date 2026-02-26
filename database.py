import datetime
import uuid
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import os

# 1. If DATABASE_URL exists -> use it.
# 2. Otherwise default to Render persistent disk path (maintaining async compatibility)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////var/data/boule_ai.db")

# 4. Maintain async SQLAlchemy compatibility for PostgreSQL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 3. Ensure directory exists before DB init: Create /var/data if missing.
if DATABASE_URL.startswith("sqlite") and "/var/data" in DATABASE_URL:
    # 5. Do NOT break local development.
    if os.name == 'nt' and not os.getenv("DATABASE_URL"):
        DATABASE_URL = "sqlite+aiosqlite:///./boule_ai.db"
    else:
        try:
            os.makedirs("/var/data", exist_ok=True)
        except OSError:
            if not os.getenv("DATABASE_URL"):
                DATABASE_URL = "sqlite+aiosqlite:///./boule_ai.db"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    chats = relationship("Chat", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", order_by="Message.timestamp")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String, ForeignKey("chats.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    deliberation_trace = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    chat = relationship("Chat", back_populates="messages")

# Async Engine Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
