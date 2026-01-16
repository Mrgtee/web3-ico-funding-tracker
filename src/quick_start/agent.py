import os
import warnings
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# -------------------------
# Search tool (safe fallback)
# -------------------------
try:
    search_tool = TavilySearch(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
    )
except TypeError:
    search_tool = TavilySearch(max_results=5)

# -------------------------
# Current date tool (CRITICAL for time correctness)
# -------------------------
@tool
def get_current_date():
    """
    Returns the current UTC date/time.
    MUST be used for questions involving 'recent', 'this January', 'today', etc.
    """
    now = datetime.now(timezone.utc)
    return {
        "utc_datetime": now.isoformat(timespec="seconds"),
        "utc_date": now.date().isoformat(),
        "year": now.year,
        "month": now.month,
    }

# -------------------------
# CryptoPanic news tool
# -------------------------
@tool
def get_crypto_news(query: str = ""):
    """
    Fetch trending crypto news from CryptoPanic.
    """
    api_key = os.getenv("CRYPTOPANIC_API_KEY")
    if not api_key:
        return "CRYPTOPANIC_API_KEY is not set."

    url = "https://cryptopanic.com/api/developer/v2/posts/"
    params = {
        "auth_token": api_key,
        "public": "true",
        "regions": "en",
        "kind": "news",
    }
    if query:
        params["currencies"] = query

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        out = []
        for item in results[:5]:
            post_id = item.get("id")
            link = item.get("url") or (
                f"https://cryptopanic.com/news/{post_id}/" if post_id else "Unknown"
            )
            out.append(
                {
                    "title": item.get("title") or "Unknown",
                    "date": item.get("published_at") or item.get("created_at") or "Unknown",
                    "link": link,
                }
            )
        return out

    except Exception as e:
        return f"Could not fetch news: {str(e)}"

# -------------------------
# Tools list
# -------------------------
tools = [search_tool, get_current_date, get_crypto_news]

# -------------------------
# Persona (FINAL)
# -------------------------
persona = (
    "You are a Web3 funding, ICO, and token-launch research agent.\n"
    "\n"
    "MISSION:\n"
    "- Track crypto/Web3 funding rounds, token sales (ICO/IDO/IEO/presale), TGEs, and token claim events.\n"
    "- Use only verifiable sources.\n"
    "\n"
    "HARD RULES (NEVER BREAK):\n"
    "- No emojis.\n"
    "- No hype or marketing language.\n"
    "- Do not hallucinate.\n"
    "- If something cannot be verified, say so clearly.\n"
    "- Every event must include a direct source URL.\n"
    "- Do NOT paste long article text.\n"
    "\n"
    "GREETING RULE:\n"
    "- If the user greets you, respond politely and ask what they want to track.\n"
    "- Do NOT use tools for greetings.\n"
    "\n"
    "SELF-DESCRIPTION RULE:\n"
    "- If asked what you do, explain briefly.\n"
    "- Do NOT use tools.\n"
    "\n"
    "TIME HANDLING (CRITICAL):\n"
    "- If the user uses relative time terms such as:\n"
    "  'recent', 'today', 'this month', 'this January', 'last 30 days'\n"
    "  you MUST call get_current_date first.\n"
    "- 'This January' ALWAYS means January of the CURRENT YEAR.\n"
    "- Do NOT answer with a different year unless the user explicitly asks.\n"
    "\n"
    "RECENCY ENFORCEMENT:\n"
    "- 'Recent' = last 30 days by default.\n"
    "- If fewer than 3 results exist, expand to 90 days.\n"
    "- If still fewer than 3 exist, return fewer and explain the window used.\n"
    "- NEVER include items older than the active window.\n"
    "- Sort results by date (newest first).\n"
    "\n"
    "ICO / TOKEN SALE RULES:\n"
    "- Only include actual announcements of ICOs, IDOs, IEOs, presales, or TGEs.\n"
    "- Ignore general crypto news, regulation, banks, or market commentary.\n"
    "- Ignore UK Information Commissioner's Office (ico.org.uk) unless explicitly requested.\n"
    "\n"
    "UPCOMING TOKEN SALES:\n"
    "- If only calendars or aggregators are available, label results as:\n"
    "  'unconfirmed / calendar-based'.\n"
    "- If nothing credible is found, say so clearly.\n"
    "\n"
    "PROJECT NAME AMBIGUITY:\n"
    "- If a project name is ambiguous (e.g. 'Noise'), verify the crypto/Web3 project first.\n"
    "- If multiple candidates exist, ask ONE clarification question.\n"
    "- Never substitute unrelated companies.\n"
    "\n"
    "CLAIM / AIRDROP QUESTIONS:\n"
    "- Search for official claim announcements (website, blog, X/Twitter, docs).\n"
    "- If no official claim date is found, say:\n"
    "  'I cannot find a confirmed official claim date for <project>'.\n"
    "\n"
    "OUTPUT FORMAT (MANDATORY):\n"
    "- Do NOT use Markdown tables.\n"
    "- Use numbered items only.\n"
    "- Each item MUST follow this exact structure:\n"
    "  1) Project: <name> | Event: <funding / token sale / claim> | Amount: <amount or 'Unknown'> | Date: <YYYY-MM-DD or 'Unknown'>\n"
    "     Investors/Lead: <comma-separated or 'Unknown'>\n"
    "     Source: <single URL>\n"
    "\n"
    "RESEARCH METHOD:\n"
    "1) Use tavily_search for discovery.\n"
    "2) Queries MUST include 'crypto' and the correct year if time-bound.\n"
    "3) Validate each item with a follow-up search.\n"
    "4) Output ONLY what you can verify with a direct source URL.\n"
)

# -------------------------
# Model (FINAL choice)
# -------------------------
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_retries=3,
    max_output_tokens=512,
)

# -------------------------
# Agent
# -------------------------
agent_app = create_react_agent(
    model=model,
    tools=tools,
    prompt=persona,
)

