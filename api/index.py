from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz
import os
import uuid
import shutil

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



def extract_text_from_pdf(file_path: str) -> str:
  doc = fitz.open(file_path)
  text = ""
  for page in doc:
    text += page.get_text()
  return text

def chunk_and_embed_text(text: str):
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
  chunks = splitter.split_text(text)
  embeddings = OpenAIEmbeddings()
  vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
  vectordb.persist()
  return vectordb



@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
  temp_file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
  with open(temp_file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  text = extract_text_from_pdf(temp_file_path)
  vectordb = chunk_and_embed_text(text)

  return {"message": "PDF uploaded and embedded successfully."}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
  vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=OpenAIEmbeddings())
  retriever = vectordb.as_retriever()

  tools = [
    Tool(
      name="DocumentSearch",
      func=lambda q: retriever.get_relevant_documents(q),
      description="Use this to look up answers from the uploaded document."
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