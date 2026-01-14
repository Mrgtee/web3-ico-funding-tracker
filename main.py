import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from src.agent import Agent # Import your specific Agent class

# --- Model Definitions for API ---
# Defines the expected JSON structure for incoming requests from Warden
class WardenRequest(BaseModel):
    query: str

# Defines the JSON structure for responses we send back to Warden
class AgentResponse(BaseModel):
    text: str

# --- FastAPI Application Setup ---
app = FastAPI(
    title="Warden Community Agent for ICO Tracking",
    description="A web server for a Gemini-powered community agent that uses Tavily and CryptoPanic.",
)

# --- Load API Keys and Initialize Your Agent ---
# Securely load the THREE correct API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")

# Check if all keys are loaded, otherwise raise a clear error
if not all([GEMINI_API_KEY, TAVILY_API_KEY, CRYPTOPANIC_API_KEY]):
    raise ValueError("One or more required API keys (GEMINI_API_KEY, TAVILY_API_KEY, CRYPTOPANIC_API_KEY) were not found in the environment variables.")

# Create an instance of your agent, passing the correct keys
agent = Agent(
    gemini_api_key=GEMINI_API_KEY,
    tavily_api_key=TAVILY_API_KEY,
    cryptopanic_api_key=CRYPTOPANIC_API_KEY
)

# --- API Endpoints ---
@app.get("/", summary="Health Check")
def health_check():
    """A simple endpoint to quickly verify that the server is running."""
    return {"status": "ok", "message": "Agent server is running"}

@app.post("/", response_model=AgentResponse, summary="Process Agent Query")
async def handle_query(request: WardenRequest):
    """
    This is the main endpoint the Warden App will call.
    """
    # Use your agent's run method to get a response
    response_text = agent.run(request.query)
    
    # Return the response in the format Warden requires: {"text": "..."}
    return AgentResponse(text=response_text)

# --- Run the Server ---
if __name__ == "__main__":
    # This allows you to run the server locally for testing
    print("Starting server... Access at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
