# main.py
from fastapi import FastAPI, Depends
from routes.auth_routes import auth_router
from routes.agent_route import agent_route 


from utils.auth import  get_current_user ,get_current_user_uuid

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(agent_route, prefix="/agent", tags=["agent"])


@app.get("/")
def read_root():
    try:
        return {
            "message": "Welcome to the Fly Zone API",
            "status": "Running",
            "code": 200,
        }
    except Exception as e:
        return {
            "message": "An error occurred",
            "error": str(e),
            "status": "Error",
            "code": 500
        }
    

@app.get("/me")
def get_my_uuid(current_user: dict = Depends(get_current_user)):
    uuid = get_current_user_uuid(current_user)
    return {"uuid": uuid}