import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Enable CORS so agentchat.vercel.app can talk to your Railway server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text: str

@app.get("/")
def home():
    return {"status": "Web3 ICO & Funding Tracker is Online", "version": "2026.1"}

# This endpoint tells the Vercel UI what "Assistant IDs" are available
@app.get("/assistants")
def list_assistants():
    return [{"assistant_id": "agent", "name": "Web3 Funding Tracker"}]

@app.post("/ask")
def ask_agent(query: Query):
    # Standard non-streaming endpoint
    response = f"Agent received: {query.text}. (Processing funding data...)"
    return {"response": response}

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    user_query = messages[-1]["content"] if messages else "Hello"
    
    # This generator follows the Vercel AI Data Stream Protocol
    async def event_generator():
        # '0' is the code for text parts in the Vercel protocol
        # We wrap the string in JSON format as required
        yield f'0:{json.dumps("Searching for latest Web3 and AI funding rounds...")}\n'
        yield f'0:{json.dumps(f"\\n\\nI am looking into your request about: {user_query}")}\n'
        
        # 'd' can be used for custom data/metadata
        yield f'd:{json.dumps({"info": "Check complete"})}\n'
        
        # '2' signals the end of the stream
        yield '2:{"finishReason":"stop"}\n'

    # Important: Set the x-vercel-ai-ui-message-stream header
    return StreamingResponse(
        event_generator(), 
        media_type="text/plain",
        headers={"x-vercel-ai-ui-message-stream": "v1"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)