# main.py
from fastapi import FastAPI

from routes.auth_routes import auth_router
from routes.agent_route import agent_route
from routes.booking_route import booking_route

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(agent_route, prefix="/agent", tags=["agent"])
app.include_router(booking_route, prefix="/bookings", tags=["bookings"])


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
    

