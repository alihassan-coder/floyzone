# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_routes import auth_router
from routes.agent_route import agent_route
from routes.booking_route import booking_route

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],  # Allow both Vite's default port and the configured port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    

