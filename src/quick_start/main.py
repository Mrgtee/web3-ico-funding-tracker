import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Your existing Agent logic imports here
# from your_agent_file import run_my_agent 

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For testing; narrow this to ["https://agentchat.vercel.app"] later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text: str

@app.get("/")
def home():
    return {"status": "Web3 ico and funding is Online", "version": "2026.1"}

@app.post("/ask")
def ask_agent(query: Query):
    # This replaces the interactive input()
    # Replace the line below with your actual agent execution call
    # response = run_my_agent(query.text)
    response = f"Agent received: {query.text}. (Logic processing...)"
    return {"response": response}

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    
    # Extract the last message content to pass to your agent
    user_query = messages[-1]["content"] if messages else ""
    
    # To work with agentchat.vercel.app, you should ideally 
    # return a stream. For a simple test, we can return a JSON 
    # that mimics the expected format:
    async def event_generator():
        # This is a simplified Mock of the Vercel AI Stream protocol
        # In a real setup, you'd use your agent.stream() logic here
        yield f'0:"Thinking about {user_query}..."\n'
        # yield your actual agent result here...
        yield '2:{"finishReason":"stop"}\n'

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    # Railway provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)