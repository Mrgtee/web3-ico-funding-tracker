import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Your existing Agent logic imports here
# from your_agent_file import run_my_agent 

load_dotenv()
app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    # Railway provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)