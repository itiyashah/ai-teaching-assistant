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
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import streamlit as st

# Safely fetch and clean database URL
DATABASE_URL = None
try:
  if "POSTGRES_URL" in st.secrets:
    DATABASE_URL = str(st.secrets["POSTGRES_URL"]).strip()
except Exception:
  pass

if not DATABASE_URL:
  DATABASE_URL = str(os.getenv("POSTGRES_URL", "sqlite:///./production_ta.db")).strip()

# Strip any accidental quotation marks wrapping the string
DATABASE_URL = DATABASE_URL.strip('"').strip("'")

# Ensure correct SQLAlchemy driver prefix for PostgreSQL
if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Ensure sslmode is present for Supabase pooled connections
if "pooler.supabase.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
  separator = "&" if "?" in DATABASE_URL else "?"
  DATABASE_URL += f"{separator}sslmode=require"

# Engine setup
if DATABASE_URL.startswith("sqlite"):
  engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
  role = Column(String, nullable=False)  # 'user' or 'assistant'
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
