from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from agent.openai_agent import ask_agent
from validation.query_validation import QueryRequest
from utils.auth import get_current_user  
from utils.jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

agent_route = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return payload  # This should be a dict with user info (e.g., {"email": ..., "id": ...})

@agent_route.post("/ask-agent")
async def agent_calling(
    request: QueryRequest, 
    current_user: dict = Depends(get_current_user) 
):
    # Print current user here if you want
    print(f"Current user in route: {current_user}")
    reply = await ask_agent(request.query, current_user)
    return {"response": reply}
