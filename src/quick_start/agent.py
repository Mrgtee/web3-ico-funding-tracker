import os
import warnings
from dotenv import load_dotenv

# This must happen before any tools are created.
load_dotenv()

import requests
from typing import Annotated, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Suppress version warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# --- 2. RESEARCH TOOL (Tavily) ---
# Now it will find the TAVILY_API_KEY from your .env
search_tool = TavilySearch(max_results=3)

# --- 3. NEWS TOOL (CryptoPanic V2) ---
@tool
def get_crypto_news(query: str = ""):
    """
    Use this tool to get trending crypto news and market sentiment from CryptoPanic.
    Input should be a currency ticker like 'BTC' or 'ETH'.
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

# --- 4. AGENT CONFIGURATION ---
from langchain_core.messages import SystemMessage # Add this import at the top

# --- 4. AGENT CONFIGURATION ---
tools = [search_tool, get_crypto_news]

# Define the persona clearly
persona = """You are Web3 ico and funding autonomous tracking and research agent.
Mission: Track funding, icos, sentiment, and project milestones.
Format: Use Markdown tables for funding data. No emojis, no hype.
Accuracy: If data is not found, say so. Do not hallucinate."""

# Initialize Gemini 2.5 Flash
# Initialize Gemini 2.5 Flash with built-in retries
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    max_retries=5,          
    timeout=60              
)

# Build the final agent using the 'checkpointer' compatible way
app = create_react_agent(
    model, 
    tools=tools, 
    prompt=persona  # Changed 'state_modifier' to 'prompt'
)