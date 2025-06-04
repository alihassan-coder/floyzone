from fastapi import APIRouter, Depends, HTTPException
from agent.openai_agent import ask_agent
from validation.query_validation import QueryRequest
from utils.auth import get_current_user  

agent_route = APIRouter()

@agent_route.post("/ask-agent")
async def agent_calling(
    request: QueryRequest, 
    current_user: dict = Depends(get_current_user) 
):
    reply = await ask_agent(request.query, current_user)
    return {"response": reply}
