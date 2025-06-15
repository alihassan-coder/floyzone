from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from agent.openai_agent import ask_agent
from validation.query_validation import QueryRequest
from utils.jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

agent_route = APIRouter()

@agent_route.post("/query")
async def agent_calling(
    request: QueryRequest,
    token: str = Depends(oauth2_scheme)
):
    try:
        # Verify the token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        reply = await ask_agent(request.query)
        return {"response": reply}
    except Exception as e:
        print(f"Error in agent_calling: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
