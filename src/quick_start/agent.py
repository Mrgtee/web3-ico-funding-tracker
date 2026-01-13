import os
import warnings
import requests
from dotenv import load_dotenv
from typing import Annotated, List, Optional

# Core LangChain, LangGraph & API imports
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# 1. Setup & Environment
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# 2. Tools Definition
search_tool = TavilySearch(max_results=3)

@tool
def get_crypto_news(query: str = ""):
    """
    Use this tool to get trending crypto news and market sentiment from CryptoPanic.
    Input should be a currency ticker like 'BTC' or 'ETH', or a project name.
    """
    api_key = os.getenv("CRYPTOPANIC_API_KEY")
    url = "https://cryptopanic.com/api/developer/v2/posts/"
    
    params = {
        "auth_token": api_key,
        "public": "true",
        "regions": "en",
        "kind": "news"
    }
    if query:
        params["currencies"] = query

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get("results", [])
        
        results = []
        for item in data[:5]:
            results.append({
                "title": item.get("title"),
                "link": item.get("url"),
                "date": item.get("published_at")
            })
        return results
    except Exception as e:
        return f"Could not fetch news: {str(e)}"

tools = [search_tool, get_crypto_news]

# 3. Persona & Model
persona = """You are a Web3 ICO and funding autonomous research agent.
Mission: Track funding, ICOs, sentiment, and project milestones.
Format: Use Markdown tables for funding data. No emojis, no hype.
Accuracy: If data is not found, say so. Do not hallucinate. 
Use your tools to find live data for every user query."""

model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

# 4. Persistence (Postgres Checkpointer)
DB_URI = os.getenv("DATABASE_URL")
connection_pool = ConnectionPool(conninfo=DB_URI, max_size=20)
checkpointer = PostgresSaver(connection_pool)
checkpointer.setup()

# 5. Compile the LangGraph Agent
agent_app = create_react_agent(
    model, 
    tools=tools, 
    prompt=persona,
    checkpointer=checkpointer
)

# 6. FastAPI Web Server
server = FastAPI(title="Web3 Funding Tracker Agent")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default-session"

class AgentChatRequest(BaseModel):
    messages: List[dict]
    thread_id: Optional[str] = "default-session"

@server.get("/")
async def health_check():
    return {"status": "online", "agent": "web3-funding-tracker"}

@server.post("/ask")
async def ask_agent(request: ChatRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {"messages": [HumanMessage(content=request.message)]}
        result = await agent_app.ainvoke(inputs, config=config)
        final_answer = result["messages"][-1].content
        return {"response": final_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

@server.post("/api/chat")
async def api_chat(request: AgentChatRequest):
    """
    AgentChat / Warden-compatible endpoint
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        user_message = request.messages[-1]["content"]
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {"messages": [HumanMessage(content=user_message)]}

        result = await agent_app.ainvoke(inputs, config=config)
        final_answer = result["messages"][-1].content

        return {
            "id": "chatcmpl-warden",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_answer
                    },
                    "finish_reason": "stop"
                }
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

# For Railway deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(server, host="0.0.0.0", port=port)
