# agentic-rag

[Demo Video](https://www.loom.com/share/de1225be6f94496a87ad2220ea47679d?sid=8d72362a-db82-47ea-8336-7d7f90f12052)

## PRD (Product Requirements Doc) – overview of the system, each tool/component, key technical choices, and how each part operates.

The agent should be able to decide when to use a given tool, or when it has a sufficient answer and can generate a final response to the user's question. However, the agent should always rely on retrieval to answer questions.
In order to enforce this behaviour, the agent is 

## Setup instructions.

Create a .env file and set your OpenAI API key.

`OPENAI_API_KEY=YOUR_KEY`

Open two separate terminal windows to run the frontend and backend parts in isolation.

To launch the FastAPI backend:

- Create and activate a virtual environment
- Run `pip install -r requirements.txt`
- Run `uvicorn api.index:app --reload` to start the FastAPI server

To launch the NextJS frontend:

- Run `npm install`
- Run `npm run next-dev` to start

The application can now be accessed at [localhost:3000](http://localhost:3000)

## Explanation of how your “agent” decides to stop searching.

The agent follows a multi-step reasoning process using its tools. It stops searching when:
- It has retrieved sufficient relevant information from the document (via the DocumentSearch tool).
- If the agent cannot find relevant information, it will ask the user for clarification using the Clarification tool.
- For calculation questions, the agent uses the MathTool and then stops once the calculation is complete and cited.

## Why you picked your libraries/services.

FastAPI

I knew I wanted to use a Python framework for the backend as the language has the best model support. I picked FastAPI over Flask 

OpenAI Embeddings

Since I was already using the OpenAI API for its chat endpoint, I felt it was most convenient to use the provided Embeddings endpoint as well.

Chroma Vector Store

I picked Chroma for developer friendliness and ease of use. It was also the most common one by far that I saw in the resources that I referenced. FAISS would be significantly better for large scale deployments of an application such as this one, but for the purposes of this exercise I thought Chroma would be sufficient.

LangChain

LangChain seemed to me to be the most flexible and developer-friendly agent framework. Pretty much every resource I read defaulted to using LangChain.

## (If implemented) how you surface the reasoning log.

When the /ask endpoint is called, the backend returns a `reasoning_log` object alongside each response, which contains a step-by-step trace of the agent's tool usage and intermediate outputs. LangChain made this fairly straightforward busing the verbose flag when initializing the agent. This log is then displayed in a window on the frontend.

## Some takeaways

I dove in pretty blind on how to approach this, so I did end up missing a pretty big part of the agent development process (i.e. taking advantage of more of LangChain's tools such as LangGraph and LangSmith)

Towards the end after I had switched to the CONVERSATIONAL_REACT_DESCRIPTION agent type, I began running into the problem of a rather rebllious agent. Because it had external memory context aside from the source document, it no longer relied on the provided tools to determine a response. Consequently, I got wildly incorrect answers and no page citations.

As such, I was trying to experiment with different ways of preserving memory across subsequent user questions, while also trying to enforce the RAG behaviour.

I suspect that a more thorough exploration of LangGraph might have allowed me to build a more obedient agent. 