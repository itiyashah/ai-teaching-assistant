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

# Safely fetch database URL from Streamlit Cloud Secrets or Environment Variables
DATABASE_URL = None
try:
  if "POSTGRES_URL" in st.secrets:
    DATABASE_URL = st.secrets["POSTGRES_URL"]
except Exception:
  pass

if not DATABASE_URL:
  DATABASE_URL = os.getenv("POSTGRES_URL", "sqlite:///./production_ta.db")

# Force SQLAlchemy to use psycopg2 driver if connecting to PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
  if "postgresql+psycopg2://" in DATABASE_URL and "?" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# Engine setup based on database type
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
