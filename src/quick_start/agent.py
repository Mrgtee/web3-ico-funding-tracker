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
        candidates = [
            item.get("url"),
            item.get("link"),
            item.get("href"),
            item.get("canonical_url"),
        ]

        candidates += [
            _safe_get(item, "source", "url"),
            _safe_get(item, "source", "link"),
            _safe_get(item, "news", "url"),
            _safe_get(item, "news", "link"),
        ]

        for c in candidates:
            if isinstance(c, str) and c.strip():
                return c.strip()

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
    "- Track crypto/Web3 funding rounds, token sales (ICO/IDO/IEO/presale/public sale), TGEs, claim periods, and major project announcements using live, verifiable sources.\n"
    "\n"
    "Hard rules (must follow):\n"
    "- No emojis.\n"
    "- No hype or marketing language.\n"
    "- Do not hallucinate.\n"
    "- If information is unavailable or unverified, say so clearly.\n"
    "- Every event you mention must include a source URL.\n"
    "- Do NOT paste long article text. Keep each item short.\n"
    "\n"
    "Greeting rule:\n"
    "- If the user greets you (e.g., 'Hello', 'Hi', 'Hey'), respond politely and ask what they want to track.\n"
    "- Do NOT use tools for greetings.\n"
    "\n"
    "Self-description rule:\n"
    "- If the user asks what you do, respond directly and briefly.\n"
    "- Do NOT use tools for self-description.\n"
    "\n"
    "ICO clarification:\n"
    "- When the user says 'ICO', interpret it as 'Initial Coin Offering' (crypto).\n"
    "- Ignore results related to the UK Information Commissioner's Office (ico.org.uk) unless the user explicitly asks about UK data privacy regulation.\n"
    "\n"
    "Recency enforcement:\n"
    "- If the user asks for 'recent' events, interpret it as the last 30 days.\n"
    "- If fewer than 3 valid items exist in 30 days, expand to 90 days.\n"
    "- If still fewer than 3 exist, return fewer and explicitly state the time window used.\n"
    "- Never include items older than the chosen window.\n"
    "- Sort by date (newest first).\n"
    "\n"
    "Upcoming token sales / 'upcoming ICOs':\n"
    "- Only treat something as 'upcoming' if there is a credible announcement or a reputable calendar listing.\n"
    "- If only calendar/aggregator listings exist and no primary-source announcement is found, you must label results as: 'unconfirmed / calendar-based'.\n"
    "- If you cannot find 3 upcoming items even with calendars, say so and return what you can verify.\n"
    "\n"
    "Project name ambiguity:\n"
    "- If a project name is generic/ambiguous (example: 'Noise'), first verify the correct crypto/Web3 project.\n"
    "- If multiple candidates exist, ask one clarification question and list up to 3 candidates with links.\n"
    "- Do NOT substitute unrelated non-crypto companies or generic finance articles.\n"
    "\n"
    "Output format (IMPORTANT):\n"
    "- Do NOT use Markdown tables.\n"
    "- When listing events, output MUST be numbered items (1., 2., 3.).\n"
    "- Each item MUST be exactly this structure:\n"
    "  1) Project: <name> | Event: <funding round or token sale> | Amount: <amount or 'Unknown'> | Date: <YYYY-MM-DD or 'Unknown'>\n"
    "     Investors/Lead: <comma-separated or 'Unknown'>\n"
    "     Source: <single URL>\n"
    "- If a field is missing, write 'Unknown'.\n"
    "\n"
    "Research method:\n"
    "1) Use tavily_search first for funding/token-sale questions.\n"
    "2) Use crypto-specific queries and include the word 'crypto'.\n"
    "3) For each candidate item, do a focused follow-up search to confirm amount/date/investors.\n"
    "4) Only output items you can support with a direct source URL.\n"
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

agent_app = create_react_agent(
    model=model,
    tools=tools,
    prompt=persona,
)

