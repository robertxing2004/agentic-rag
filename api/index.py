from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz
import os
import uuid
import shutil
from dotenv import load_dotenv

load_dotenv()

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
CHROMA_DIR = "./chroma_store"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)



def extract_text_from_pdf(file_path: str) -> list:
  doc = fitz.open(file_path)
  pages = []
  for page_num, page in enumerate(doc, 1):
    text = page.get_text()
    if text.strip():  # Only add non-empty pages
      pages.append({"page": page_num, "text": text})
  return pages

def chunk_and_embed_text(pages: list):
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
  all_chunks = []
  all_metadata = []
  
  for page_data in pages:
    page_num = page_data["page"]
    text = page_data["text"]
    chunks = splitter.split_text(text)
    
    for chunk in chunks:
      all_chunks.append(chunk)
      all_metadata.append({"page": page_num})
  
  embeddings = OpenAIEmbeddings()
  vectordb = Chroma.from_texts(
    all_chunks, 
    embedding=embeddings, 
    persist_directory=CHROMA_DIR,
    metadatas=all_metadata
  )
  vectordb.persist()
  return vectordb

def search_documents_with_citations(query: str):
  vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=OpenAIEmbeddings())
  retriever = vectordb.as_retriever(search_kwargs={"k": 5})
  docs = retriever.get_relevant_documents(query)
  
  # Group by page and format with citations
  page_content = {}
  for doc in docs:
    page_num = doc.metadata.get("page", "Unknown")
    if page_num not in page_content:
      page_content[page_num] = []
    page_content[page_num].append(doc.page_content)
  
  # Format response with page citations
  response_parts = []
  # Convert page numbers to int for sorting, handle "Unknown" case
  sorted_pages = sorted(page_content.keys(), key=lambda x: int(x) if str(x).isdigit() else float('inf'))
  for page_num in sorted_pages:
    content = " ".join(page_content[page_num])
    response_parts.append(f"[Page {page_num}]: {content}")
  
  return "\n\n".join(response_parts)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
  temp_file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
  with open(temp_file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  pages = extract_text_from_pdf(temp_file_path)
  vectordb = chunk_and_embed_text(pages)

  return {"message": "PDF uploaded and embedded successfully."}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
  tools = [
    Tool(
      name="DocumentSearch",
      func=search_documents_with_citations,
      description="Use this to look up answers from the uploaded document. Returns content with page citations."
    ),
    Tool(
      name="Calculator",
      func=lambda expr: str(eval(expr)),
      description="Use this to evaluate simple math expressions."
    )
  ]

  llm = ChatOpenAI(model="gpt-4", temperature=0)

  agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
  )

  response = agent.run(question)
  return {"answer": response}