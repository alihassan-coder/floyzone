from fastapi import APIRouter
from agent.openai_agent import ask_agent
from validation.query_validation import QueryRequest

import asyncio

agent_route = APIRouter()

@agent_route.post("/ask-agent")
async def agent_calling(request: QueryRequest):
    reply = await ask_agent(request.query)
    return {"response": reply}

