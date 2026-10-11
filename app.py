import json
import os
import re
import uuid
from agent import build_teaching_assistant_graph
from database import (
    Conversation,
    Message,
    SessionLocal,
    User,
    WeakTopic,
    init_db,
)
from dotenv import load_dotenv
from rag import setup_vector_database
import streamlit as st

load_dotenv()
init_db()

st.set_page_config(
    page_title="AI Teaching Assistant - Pink Edition",
    page_icon="🌸",
    layout="wide",
)

# --- CUSTOM PINK THEME CSS INJECTION ---
st.markdown(
    """
    <style>
        /* Main App Background & Font */
        .stApp {
            background-color: #fff0f5; /* Light lavender-pink tint */
            color: #4a2e35;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffe4e1; /* Soft misty rose pink */
            border-right: 2px solid #ffb6c1;
        }

        /* Headers & Text */
        h1, h2, h3, h4, h5, h6, span, p {
            color: #5c3a42 !important;
        }

        /* Buttons (Sidebar and general) */
        .stButton>button {
            background-color: #ffb6c1 !important;
            color: #5c3a42 !important;
            border: 1px solid #ff69b4 !important;
            border-radius: 8px !important;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #ff69b4 !important;
            color: white !important;
            border-color: #db7093 !important;
        }

        /* Input Fields & Text Areas */
        .stTextInput>div>div>input, .stChatInput input {
            background-color: #ffffff !important;
            color: #4a2e35 !important;
            border: 1.5px solid #ffb6c1 !important;
            border-radius: 8px !important;
        }
        .stTextInput>div>div>input:focus {
            border-color: #ff1493 !important;
            box-shadow: 0 0 5px rgba(255, 20, 147, 0.3);
        }

        /* Chat Bubbles Styling */
        [data-testid="stChatMessage"] {
            background-color: #ffffff;
            border: 1px solid #ffc0cb;
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(255, 182, 193, 0.2);
        }

        /* Checkboxes */
        .stCheckbox span {
            color: #5c3a42 !important;
            font-weight: 500;
        }

        /* File Uploader box */
        [data-testid="stFileUploader"] {
            background-color: #fff0f5;
            border: 2px dashed #ffb6c1;
            border-radius: 10px;
            padding: 10px;
        }
    </style>
""",
    unsafe_allow_html=True,
)


def format_math_equations(text):
  text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
  text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.DOTALL)
  return text


if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""
if "current_chat_id" not in st.session_state:
  st.session_state.current_chat_id = None

db_session = SessionLocal()

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
  st.title("🌸 AI Teaching Assistant - Login")
  with st.form("login"):
    uname = st.text_input("Enter Username:")
    if st.form_submit_button("Start Learning 💖"):
      cleaned_name = uname.strip()
      if cleaned_name:
        user = (
            db_session.query(User).filter(User.username == cleaned_name).first()
        )
        if not user:
          user = User(username=cleaned_name)
          db_session.add(user)
          db_session.commit()
          db_session.refresh(user)

        st.session_state.username = cleaned_name
        st.session_state.logged_in = True
        db_session.close()
        st.rerun()
else:
  user = (
      db_session.query(User)
      .filter(User.username == st.session_state.username)
      .first()
  )

  # --- SIDEBAR & CHAT MANAGEMENT ---
  st.sidebar.title(f"👤 {user.username}")
  if st.sidebar.button("Log Out 🚪"):
    db_session.close()
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.current_chat_id = None
    st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.header("⚙️ Configuration")
  uploaded_file = st.sidebar.file_uploader(
      "Upload Textbook/Lecture PDF (Optional)", type="pdf"
  )

  st.sidebar.markdown("---")
  st.sidebar.subheader("💬 Chat History Threads")

  if st.sidebar.button("➕ New Chat Session", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    new_chat = Conversation(
        id=new_id, user_id=user.id, title="New Chat", pinned=False
    )
    db_session.add(new_chat)
    db_session.commit()
    st.session_state.current_chat_id = new_id
    st.rerun()

  user_chats = (
      db_session.query(Conversation)
      .filter(Conversation.user_id == user.id)
      .order_by(Conversation.pinned.desc(), Conversation.created_at.desc())
      .all()
  )

  if not user_chats:
    default_id = str(uuid.uuid4())[:8]
    default_chat = Conversation(
        id=default_id, user_id=user.id, title="New Chat", pinned=False
    )
    db_session.add(default_chat)
    db_session.commit()
    st.session_state.current_chat_id = default_id
    user_chats = [default_chat]
  elif (
      not st.session_state.current_chat_id
      or not db_session.query(Conversation)
      .filter(Conversation.id == st.session_state.current_chat_id)
      .first()
  ):
    st.session_state.current_chat_id = user_chats[0].id

  for chat in user_chats:
    pin_label = "📌" if chat.pinned else "📍"
    cols = st.sidebar.columns([0.62, 0.19, 0.19])

    with cols[0]:
      display_title = f"⭐ {chat.title}" if chat.pinned else chat.title
      if st.button(
          display_title, key=f"select_{chat.id}", use_container_width=True
      ):
        st.session_state.current_chat_id = chat.id
        st.rerun()
    with cols[1]:
      if st.button(pin_label, key=f"pin_{chat.id}", help="Pin / Unpin chat"):
        chat.pinned = not chat.pinned
        db_session.commit()
        st.rerun()
    with cols[2]:
      if st.button("✏️", key=f"rename_btn_{chat.id}", help="Rename chat"):
        st.session_state[f"editing_{chat.id}"] = not st.session_state.get(
            f"editing_{chat.id}", False
        )
        st.rerun()

    if st.session_state.get(f"editing_{chat.id}", False):
      new_title = st.sidebar.text_input(
          "Rename to:", value=chat.title, key=f"input_rename_{chat.id}"
      )
      if st.sidebar.button("Save Title", key=f"save_rename_{chat.id}"):
        if new_title.strip():
          chat.title = new_title.strip()
          db_session.commit()
          st.session_state[f"editing_{chat.id}"] = False
          st.rerun()

  # --- MAIN CHAT INTERFACE ---
  st.title("🌸 AI Teaching Assistant")
  st.markdown("Your elegant intelligent study companion.")

  active_chat = (
      db_session.query(Conversation)
      .filter(Conversation.id == st.session_state.current_chat_id)
      .first()
  )
  messages = (
      db_session.query(Message)
      .filter(Message.conversation_id == active_chat.id)
      .order_by(Message.timestamp.asc())
      .all()
  )

  user_weak_topics_objs = (
      db_session.query(WeakTopic).filter(WeakTopic.user_id == user.id).all()
  )
  user_weak_topics = [wt.topic_query for wt in user_weak_topics_objs]

  for idx, msg in enumerate(messages):
    with st.chat_message(msg.role):
      formatted_content = format_math_equations(msg.content)
      st.markdown(formatted_content)

      if msg.role == "assistant" and idx > 0:
        user_query_text = messages[idx - 1].content
        is_already_weak = user_query_text in user_weak_topics

        mark_weak = st.checkbox(
            "📌 Save to Weak Topics Memory",
            value=is_already_weak,
            key=f"weak_toggle_{active_chat.id}_{msg.id}",
        )

        if mark_weak and not is_already_weak:
          new_wt = WeakTopic(user_id=user.id, topic_query=user_query_text)
          db_session.add(new_wt)
          db_session.commit()
          st.success("Added to Weak Topics! 💖")
          st.rerun()
        elif not mark_weak and is_already_weak:
          db_session.query(WeakTopic).filter(
              WeakTopic.user_id == user.id,
              WeakTopic.topic_query == user_query_text,
          ).delete()
          db_session.commit()
          st.info("Removed from Weak Topics.")
          st.rerun()

  if prompt := st.chat_input(
      "Ask a question or request a practice problem..."
  ):
    if len(messages) == 0 or active_chat.title == "New Chat":
      active_chat.title = (
          prompt[:22] + "..." if len(prompt) > 22 else prompt
      )

    user_msg = Message(
        conversation_id=active_chat.id, role="user", content=prompt
    )
    db_session.add(user_msg)
    db_session.commit()

    with st.chat_message("user"):
      st.markdown(prompt)

    with st.chat_message("assistant"):
      with st.spinner("Thinking... 💭"):
        retriever = (
            setup_vector_database(uploaded_file)
            if uploaded_file is not None
            else None
        )
        app_graph = build_teaching_assistant_graph(retriever)

        past_history = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        initial_state = {
            "messages": past_history,
            "student_query": prompt,
            "retrieved_context": "",
            "generated_output": "",
            "critique": "",
            "reflection_count": 0,
            "weak_topics": user_weak_topics,
        }

        result = app_graph.invoke(initial_state)
        ai_response = result.get("generated_output")

        formatted_ai_response = format_math_equations(ai_response)
        st.markdown(formatted_ai_response)

        ai_msg = Message(
            conversation_id=active_chat.id,
            role="assistant",
            content=ai_response,
        )
        db_session.add(ai_msg)
        db_session.commit()

        st.rerun()

  # Sidebar Weak Topics
  st.sidebar.markdown("---")
  st.sidebar.subheader("🧠 Weak Topics Memory")
  if user_weak_topics:
    for idx, wt in enumerate(user_weak_topics):
      st.sidebar.markdown(f"{idx+1}. {wt}")
  else:
    st.sidebar.info("No weak topics logged yet.")

db_session.close()