import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL", "sqlite:///./production_ta.db")

# Force the psycopg2 driver for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgres://", "postgresql+psycopg2://", 1
  )
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith(
    "postgresql+psycopg2://"
):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+psycopg2://", 1
  )

# SQLite needs a specific thread flag; PostgreSQL does not
if DATABASE_URL.startswith("sqlite"):
  engine = create_engine(
      DATABASE_URL, connect_args={"check_same_thread": False}
  )
else:
  engine = create_engine(
      DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True
  )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- DATABASE MODELS ---
class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(100), unique=True, index=True, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  conversations = relationship(
      "Conversation", back_populates="owner", cascade="all, delete-orphan"
  )
  weak_topics = relationship(
      "WeakTopic", back_populates="owner", cascade="all, delete-orphan"
  )


class Conversation(Base):
  __tablename__ = "conversations"

  id = Column(String(50), primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  title = Column(String(255), default="New Chat")
  pinned = Column(Boolean, default=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  owner = relationship("User", back_populates="conversations")
  messages = relationship(
      "Message", back_populates="conversation", cascade="all, delete-orphan"
  )


class Message(Base):
  __tablename__ = "messages"

  id = Column(Integer, primary_key=True, index=True)
  conversation_id = Column(String(50), ForeignKey("conversations.id"), index=True)
  role = Column(String(20), nullable=False)  # 'user' or 'assistant'
  content = Column(Text, nullable=False)
  timestamp = Column(DateTime, default=datetime.utcnow)

  conversation = relationship("Conversation", back_populates="messages")


class WeakTopic(Base):
  __tablename__ = "weak_topics"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), index=True)
  topic_query = Column(Text, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  owner = relationship("User", back_populates="weak_topics")


# Initialize tables in DB
def init_db():
  Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    return db
  finally:
    pass  # Management handled in app context
