import os
import warnings
import requests
from dotenv import load_dotenv
from typing import Annotated, List

# Core LangChain & LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

# 1. Setup
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# 2. Tools
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

# 3. Persona
persona = """You are a Web3 ICO and funding autonomous research agent.
Mission: Track funding, ICOs, sentiment, and project milestones.
Format: Use Markdown tables for funding data. No emojis, no hype.
Accuracy: If data is not found, say so. Do not hallucinate. 
Use your tools to find live data for every user query."""

# 4. Model & Agent (Updated for 2026)
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # The latest stable flagship in 2026
    temperature=0,
    max_retries=5,          
    timeout=60              
)

# The 'app' variable is what langgraph.json points to
app = create_react_agent(
    model, 
    tools=tools, 
    prompt=persona
)