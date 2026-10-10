import os
import operator
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

# Load environment variables from .env file
load_dotenv()


class AgentState(TypedDict):
  messages: Annotated[List[dict], operator.add]
  student_query: str
  retrieved_context: str
  generated_output: str
  critique: str
  reflection_count: int
  weak_topics: List[str]


def retrieval_node(state: AgentState, retriever):
  query = state["student_query"]
  if retriever is not None:
    docs = retriever.invoke(query)
    context = "\n".join([doc.page_content for doc in docs])
  else:
    context = (
        "No textbook PDF uploaded for this session. Use general mathematical and"
        " domain knowledge."
    )
  return {"retrieved_context": context}


def generator_node(state: AgentState, groq_api_key: str = None):
  query = state["student_query"]
  context = state.get("retrieved_context", "")
  chat_history = state.get("messages", [])
  weak_topics = state.get("weak_topics", [])

  # Fallback to environment variable if groq_api_key is not passed
  api_key = groq_api_key or os.getenv("GROQ_API_KEY")

  llm = ChatGroq(
      model="openai/gpt-oss-20b", groq_api_key=api_key, temperature=0.1
  )

  messages = [
      SystemMessage(
          content=(
              "You are an expert AI Teaching Assistant. Answer the student's"
              " query accurately using the provided textbook context (if"
              " available) and past conversation history. Format all"
              " mathematical equations using standard LaTeX enclosed in double"
              " dollar signs ($$ ... $$) for block equations or single dollar"
              " signs ($ ... $) for inline equations so they render correctly."
          )
      )
  ]

  for msg in chat_history:
    if msg["role"] == "user":
      messages.append(HumanMessage(content=msg["content"]))
    else:
      messages.append(AIMessage(content=msg["content"]))

  messages.append(
      HumanMessage(
          content=(
              f"Context:\n{context}\n\nCurrent Student Query: {query}\n\nPast"
              f" weak topics to note if relevant: {weak_topics}"
          )
      )
  )

  response = llm.invoke(messages)
  return {"generated_output": response.content}


def reflection_node(state: AgentState, groq_api_key: str = None):
  output = state["generated_output"]
  count = state.get("reflection_count", 0)

  api_key = groq_api_key or os.getenv("GROQ_API_KEY")

  llm = ChatGroq(
      model="openai/gpt-oss-20b", groq_api_key=api_key, temperature=0.0
  )
  critique_prompt = f"Review this explanation for mathematical accuracy and clarity:\n\n{output}\n\nIf it is accurate and complete, output 'PASS'. If it needs more detail or has errors, output 'REVISE: [reason]'."

  response = llm.invoke([HumanMessage(content=critique_prompt)])
  return {"critique": response.content, "reflection_count": count + 1}


def should_reflect(state: AgentState):
  if "REVISE" in state["critique"] and state.get("reflection_count", 0) < 2:
    return "revise"
  return "proceed"


def memory_update_node(state: AgentState):
  query = state["student_query"]
  weak_topics = state.get("weak_topics", [])
  if any(
      w in query.lower()
      for w in ["struggle", "hard", "confused", "don't understand"]
  ):
    weak_topics.append(query)
  return {"weak_topics": list(set(weak_topics))}


def build_teaching_assistant_graph(retriever, groq_api_key: str = None):
  workflow = StateGraph(AgentState)

  workflow.add_node(
      "retrieval", lambda state: retrieval_node(state, retriever)
  )
  workflow.add_node(
      "generator", lambda state: generator_node(state, groq_api_key)
  )
  workflow.add_node(
      "reflection", lambda state: reflection_node(state, groq_api_key)
  )
  workflow.add_node("memory_update", memory_update_node)

  workflow.set_entry_point("retrieval")
  workflow.add_edge("retrieval", "generator")
  workflow.add_edge("generator", "reflection")

  workflow.add_conditional_edges(
      "reflection",
      should_reflect,
      {"revise": "generator", "proceed": "memory_update"},
  )

  workflow.add_edge("memory_update", END)
  return workflow.compile()