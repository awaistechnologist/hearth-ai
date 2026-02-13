import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.orchestrator import Orchestrator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

app = FastAPI(title="Hearth Brain API")
orchestrator = None

class ChatRequest(BaseModel):
    user_id: str
    user_name: str = "User"
    text: str

class ChatResponse(BaseModel):
    response: str

@app.on_event("startup")
async def startup_event():
    global orchestrator
    logger.info("Initializing Heart Brain...")
    orchestrator = Orchestrator()
    logger.info("Brain Online.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main entry point for Home Assistant to talk to Hearth.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Brain initializing...")
    
    logger.info(f"Received request from {request.user_id}: {request.text}")
    
    response_text = await orchestrator.process(
        user_id=request.user_id,
        user_name=request.user_name,
        text=request.text
    )
    
    return ChatResponse(response=response_text)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
