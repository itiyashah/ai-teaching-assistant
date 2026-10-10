import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def setup_vector_database(uploaded_file):
  os.makedirs("./temp", exist_ok=True)
  file_path = os.path.join("./temp", uploaded_file.name)
  with open(file_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

  loader = PyPDFLoader(file_path)
  pages = loader.load()

  text_splitter = RecursiveCharacterTextSplitter(
      chunk_size=500, chunk_overlap=50
  )
  docs = text_splitter.split_documents(pages)

  # Free local sentence-transformer embeddings (No API key needed!)
  embeddings = HuggingFaceEmbeddings(
      model_name="all-MiniLM-L6-v2"
  )
  vector_store = Chroma.from_documents(docs, embeddings)

  return vector_store.as_retriever(search_kwargs={"k": 3})