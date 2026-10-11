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

# 1. Fetch URL from Streamlit Secrets or Environment Variables
DATABASE_URL = None
try:
  if hasattr(st, "secrets") and "POSTGRES_URL" in st.secrets:
    DATABASE_URL = str(st.secrets["POSTGRES_URL"]).strip()
except Exception:
  pass

if not DATABASE_URL:
  DATABASE_URL = str(os.getenv("POSTGRES_URL", "")).strip()

# Clean quotes if any exist
DATABASE_URL = DATABASE_URL.strip('"').strip("'")

# 2. Force PostgreSQL driver and ensure SSL mode for Supabase
if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+psycopg2://", 1
  )

if "pooler.supabase.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
  separator = "&" if "?" in DATABASE_URL else "?"
  DATABASE_URL += f"{separator}sslmode=require"

# Fallback alert if no valid URL is found
if not DATABASE_URL or not DATABASE_URL.startswith("postgresql"):
  raise ValueError(
      "CRITICAL: Supabase POSTGRES_URL is missing or incorrectly formatted in"
      " Streamlit Secrets!"
  )

# 3. Create Engine for Supabase
engine = create_engine(
    DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True
)

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
