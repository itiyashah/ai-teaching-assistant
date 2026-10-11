from datetime import datetime
import os
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
from sqlalchemy.orm import declarative_base, sessionmaker
import streamlit as st

# Safely extract POSTGRES_URL from Streamlit Secrets or environment
DATABASE_URL = None
try:
  if hasattr(st, "secrets") and "POSTGRES_URL" in st.secrets:
    DATABASE_URL = str(st.secrets["POSTGRES_URL"]).strip()
except Exception:
  pass

if not DATABASE_URL:
  DATABASE_URL = str(os.getenv("POSTGRES_URL", "")).strip()

# Clean any accidental quotes
DATABASE_URL = DATABASE_URL.strip('"').strip("'")

# Fallback to local SQLite if URL is completely missing so app doesn't crash
if not DATABASE_URL:
  DATABASE_URL = "sqlite:///./production_ta.db"

# Ensure correct psycopg2 driver prefix
if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgres://", "postgresql+psycopg2://", 1
  )
elif DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+psycopg2://", 1
  )

# Initialize Engine
if DATABASE_URL.startswith("sqlite"):
  engine = create_engine(
      DATABASE_URL, connect_args={"check_same_thread": False}
  )
else:
  engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- DATABASE MODELS ---
class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String, unique=True, index=True, nullable=False)


class Conversation(Base):
  __tablename__ = "conversations"
  id = Column(String, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  title = Column(String, default="New Chat")
  pinned = Column(Boolean, default=False)
  created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
  __tablename__ = "messages"
  id = Column(Integer, primary_key=True, index=True)
  conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
  role = Column(String, nullable=False)
  content = Column(Text, nullable=False)
  timestamp = Column(DateTime, default=datetime.utcnow)


class WeakTopic(Base):
  __tablename__ = "weak_topics"
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  topic_query = Column(Text, nullable=False)


# --- INITIALIZATION & SESSION HELPERS ---
def init_db():
  Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
