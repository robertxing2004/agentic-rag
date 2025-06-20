from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz
import os
import uuid
import shutil
from dotenv import load_dotenv
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferMemory
from collections import defaultdict

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

session_memories = defaultdict(lambda: ConversationBufferMemory(memory_key="chat_history", return_messages=True))

class ReasoningLogHandler(BaseCallbackHandler):
  def __init__(self):
    self.logs = []

  def on_tool_start(self, serialized, input_str, **kwargs):
    self.logs.append(f"Tool called: {serialized['name']} with input: {input_str}")

  def on_text(self, text, **kwargs):
    if text.strip():
      self.logs.append(f"Agent: {text.strip()}")



# pdf upload and embed
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



# agent tool implementations
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

def math_tool(query: str):
  llm = ChatOpenAI(model="gpt-4", temperature=0)
  prompt = (
    "You are a math and date calculation assistant. "
    "Interpret and solve the following problem, showing your reasoning. "
    "If the question involves dates or durations, calculate accordingly. "
    "Question: " + query
  )
  return llm.invoke(prompt)

def clarification(clarification_request: str):
    # Return a dict so the frontend can distinguish this as a clarification
    return {"clarification": f"Could you please clarify: {clarification_request}"}



# pdf upload endpoint
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
  temp_file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
  with open(temp_file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  pages = extract_text_from_pdf(temp_file_path)
  vectordb = chunk_and_embed_text(pages)

  return {"message": "PDF uploaded and embedded successfully."}

# question endpoint
@app.post("/ask")
async def ask_question(request: Request):
  form = await request.form()
  question = form.get("question")
  session_id = form.get("session_id", "default")  # Use a real session/user id in production

  memory = session_memories[session_id]

  tools = [
    Tool(
      name="DocumentSearch",
      func=search_documents_with_citations,
      description="Use this to look up answers from the uploaded document. Return content with page citations."
    ),
    Tool(
      name="MathTool",
      func=math_tool,
      description="Use this to solve calculation problems described in natural language."
    ),
    Tool(
      name="Clarification",
      func=clarification,
      description="Use this to ask the user for more information or clarification if the question is ambiguous or missing details. Pass a message describing what you need clarified."
    )
  ]

  llm = ChatOpenAI(model="gpt-4", temperature=0)

  system_prompt = """
    You are a helpful AI assistant that answers questions based on uploaded documents. You should remember the previous conversation and use it to inform your answers.

    IMPORTANT INSTRUCTIONS:
    1. You MUST use the DocumentSearch tool to find relevant information from the uploaded documents.
    2. When providing answers, ALWAYS cite the specific page numbers where you found the information.
    3. Format your response clearly with proper citations like: "According to page X..."
    4. If you find information on multiple pages, cite all relevant pages.
    5. If you cannot find relevant information in the documents, say so clearly.
    6. Use the Clarification tool to ask the user for extra context.
    7. Use the MathTool tool only for mathematical calculations when needed.

    Example tool output:
    [Page 2]: [your answer].

    Example response format:
    "Based on the document, [your answer]. This information can be found on page 2."
  """

  agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    agent_kwargs={"system_message": system_prompt},
    memory=memory
  )

  reasoning_handler = ReasoningLogHandler()
  response = agent.run(question, callbacks=[reasoning_handler])

  clarification_msg = None
  answer = response
  if isinstance(response, dict) and "clarification" in response:
    clarification_msg = response["clarification"]
    answer = ""  # No normal answer in this case

  return {
    "answer": answer,
    "clarification": clarification_msg,
    "reasoning_log": reasoning_handler.logs
  }