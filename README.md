
# 🌸 AI Teaching Assistant - Pink Edition

An intelligent, elegant study companion built with **Streamlit**, **LangGraph**, **Groq AI**, and **Supabase PostgreSQL**. It features persistent chat history, PDF document context ingestion (RAG), math equation formatting, and a dedicated weak-topics memory tracker.

---
### live link : https://ai-teaching-assistant-projects.streamlit.app/

## ✨ Features

- **💖 Custom Pink Aesthetic**: Designed with a cozy, polished pink theme and custom CSS injection.
- **☁️ Cloud Database Persistence**: Seamlessly stores users, chat threads, messages, and weak topics using **Supabase PostgreSQL** (with automatic fallback support).
- **📚 RAG-Powered PDF Learning**: Upload textbooks or lecture notes (`.pdf`) to query specific course material using Hugging Face embeddings.
- **🧠 Weak Topics Tracker**: Pin difficult questions and queries to review later in your personalized study memory.
- **📐 LaTeX Math Support**: Automatically formats mathematical expressions for clear readability.

---

## 🛠️ Tech Stack

- **Frontend & UI**: [Streamlit](https://streamlit.io/)
- **Orchestration & AI**: [LangChain](https://www.langchain.com/) / [LangGraph](https://www.langchain.com/langgraph) & [Groq API](https://groq.com/)
- **Database & ORM**: PostgreSQL ([Supabase](https://supabase.com/)) & [SQLAlchemy](https://www.sqlalchemy.org/)
- **Embeddings & Vector Store**: Hugging Face (`sentence-transformers`) & ChromaDB

---

## 🚀 Getting Started Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/itiyashah/ai-teaching-assistant.git](https://github.com/itiyashah/ai-teaching-assistant.git)
cd ai-teaching-assistant
