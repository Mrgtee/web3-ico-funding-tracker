import os
import warnings
import requests
from dotenv import load_dotenv
from typing import List, Optional

# Core LangChain & LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.server import create_app

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row  # REQUIRED

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
Use your tools to find live data for every user query.
"""

model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

# 4. Persistence (Postgres Checkpointer)
DB_URI = os.getenv("DATABASE_URL")
checkpointer = None

if DB_URI:
    try:
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        }

        connection_pool = ConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs=connection_kwargs
        )

        checkpointer = PostgresSaver(connection_pool)

        try:
            checkpointer.setup()
            print("Database connected and tables verified.")
        except Exception as setup_err:
            print(f"Database connected but setup failed: {setup_err}")

    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
else:
    print("WARNING: DATABASE_URL not set. Agent will run without memory.")

# 5. Compile the LangGraph Agent
agent = create_react_agent(
    model,
    tools=tools,
    prompt=persona,
    checkpointer=checkpointer
)

# 6. LangGraph Server (Warden-compatible)
app = create_app(
    agent,
    assistant_id="web3-funding-tracker",
    title="Web3 ICO Funding Tracker",
    description="Autonomous Web3 funding, ICO, and sentiment research agent"
)

# 7. Railway entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
