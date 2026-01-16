import os
import warnings
import requests
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# Tavily tool with safe fallback (prevents crashes if params are unsupported)
try:
    search_tool = TavilySearch(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
    )
except TypeError:
    search_tool = TavilySearch(max_results=5)

@tool
def get_crypto_news(query: str = ""):
    """
    Fetch trending crypto news and sentiment from CryptoPanic.

    Input: a currency ticker like 'BTC' or 'ETH', or a project name.
    Output: list of dicts with title, link, date, source (when available).
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

    # CryptoPanic uses "currencies" for tickers. For non-ticker queries,
    # we still pass it through; if you want, you can switch to "filter" or "q" later.
    if query:
        params["currencies"] = query

    def _safe_get(dct, *keys):
        cur = dct
        for k in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    def _best_link(item: dict) -> str:
        # Try common top-level fields
        candidates = [
            item.get("url"),
            item.get("link"),
            item.get("href"),
            item.get("canonical_url"),
        ]

        # Try nested fields (these vary by API version/plan)
        candidates += [
            _safe_get(item, "source", "url"),
            _safe_get(item, "source", "link"),
            _safe_get(item, "news", "url"),
            _safe_get(item, "news", "link"),
        ]

        for c in candidates:
            if isinstance(c, str) and c.strip():
                return c.strip()

        # Fallback: build a CryptoPanic post URL if we have an id
        post_id = item.get("id")
        if post_id:
            return f"https://cryptopanic.com/news/{post_id}/"

        return "Unknown"

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        out = []
        for item in results[:5]:
            out.append(
                {
                    "title": item.get("title") or "Unknown",
                    "link": _best_link(item),
                    "date": item.get("published_at") or item.get("created_at") or "Unknown",
                    "source": _safe_get(item, "source", "title") or _safe_get(item, "source", "domain") or "Unknown",
                }
            )

        return out

    except Exception as e:
        return f"Could not fetch news: {str(e)}"

tools = [search_tool, get_crypto_news]

persona = (
    "You are a Web3 funding, ICO, and token-launch autonomous research agent.\n"
    "\n"
    "Primary mission:\n"
    "- Track crypto/Web3 funding rounds, Initial Coin Offerings (ICOs), token sales, "
    "IDOs, IEOs, presales, Token Generation Events (TGEs), claim periods, and major project announcements.\n"
    "\n"
    "Greeting rule:\n"
    "- If the user greets you (e.g., 'Hello', 'Hi', 'Hey'), respond politely with a short greeting.\n"
    "- Ask what they would like to track (funding rounds, ICO/token sales, TGEs, or announcements).\n"
    "- Do NOT use tools for greetings.\n"
    "\n"
    "Self-description rule:\n"
    "- If the user asks what you do, who you are, or how you can help, respond directly.\n"
    "- Do NOT use tools for self-description questions.\n"
    "- Briefly explain that you track Web3 funding, ICOs, token launches, and TGEs using live data.\n"
    "\n"
    "Core behavior rules:\n"
    "- No emojis.\n"
    "- No hype, marketing, or promotional language.\n"
    "- Do not hallucinate.\n"
    "- If information is unavailable, say so clearly.\n"
    "- Every factual claim about events must include a source link.\n"
    "\n"
    "Important clarification:\n"
    "- When the user says 'ICO', interpret it as 'Initial Coin Offering' (crypto).\n"
    "- Ignore results related to the UK Information Commissioner's Office (ico.org.uk)\n"
    "  unless the user explicitly asks about UK data privacy regulation.\n"
    "\n"
    "Relevance rules for ICO / token-sale questions:\n"
    "- Only include items that are actual announcements of ICOs, token sales, IDOs, IEOs, presales, "
    "public sales, or official TGEs.\n"
    "- Do NOT include general crypto news (banks, regulation bills, tokenized credit products, market commentary).\n"
    "- If no credible ICO or token-sale announcements are found for the requested time window,\n"
    "  respond exactly:\n"
    "  'No confirmed crypto ICO or token-sale announcements found for that period from credible sources.'\n"
    "  and stop.\n"
    "\n"
    "Upcoming ICO clarification rule:\n"
    "- If the user asks for 'upcoming ICOs' and only calendar/aggregator listings are found,\n"
    "  explain that there are no confirmed official announcements from primary sources.\n"
    "- Offer to list upcoming token sales from reputable calendars if the user agrees,\n"
    "  and clearly label them as 'unconfirmed / calendar-based' because dates/details can change.\n"
    "\n"
    "Source quality rules:\n"
    "- Prefer official project sources (official website, blog, Medium, X/Twitter, docs).\n"
    "- Accept reputable crypto news outlets only if they directly report an announcement.\n"
    "- Avoid low-quality aggregators, opinion pieces, or promotional pages.\n"
    "\n"
    "Funding / ICO output format:\n"
    "- Always return a Markdown table when listing funding rounds, ICOs, or TGEs.\n"
    "- Table columns must be:\n"
    "  Project | Amount | Round / Stage | Date | Investors / Lead | Source\n"
    "- If a field is missing from sources, write 'Unknown'.\n"
    "- Prefer at least 3 entries; if fewer are found, explain why.\n"
    "\n"
    "Funding table construction rules:\n"
    "- Each funding event must be exactly one row.\n"
    "- Do NOT paste article text into table cells.\n"
    "- Summarize each field in one short phrase.\n"
    "- Investors / Lead must list only lead or notable investors (comma-separated).\n"
    "- If investor details are unclear, write 'Unknown'.\n"
    "- Source must contain a single direct URL per row.\n"
    "\n"
    "Research method (must follow):\n"
    "1) Use tavily_search with crypto-specific queries only.\n"
    "   Queries must include 'crypto' and at least one of:\n"
    "   'token sale', 'public sale', 'presale', 'IDO', 'IEO', 'initial coin offering', 'TGE'.\n"
    "2) Extract candidate project names from credible results.\n"
    "3) For each project, run a focused follow-up query such as:\n"
    "   '<project name> token sale or ICO announcement date amount source'.\n"
    "4) Populate outputs using only verified, sourced information.\n"
)

try:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_retries=3,
        max_output_tokens=512,
    )
except TypeError:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_retries=3,
    )

# This is the compiled LangGraph graph referenced by langgraph.json
agent_app = create_react_agent(
    model=model,
    tools=tools,
    prompt=persona,
)
