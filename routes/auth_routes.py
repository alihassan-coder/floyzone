from fastapi import APIRouter, HTTPException
from config.database import db
from validation.user_validation import UserRegister, UserLogin
from utils.hash import hash_password, verify_password

auth_router = APIRouter()


@auth_router.post("/register")
def register_user(user: UserRegister):
    try:
        existing_user = db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered.")

        user_dict = user.dict()
        user_dict["password"] = hash_password(user.password)
        db.users.insert_one(user_dict)

        return {
            "status": "success", 
            "message": "User registered successfully",
            "code": 201
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@auth_router.post("/login")
def login_user(user: UserLogin):
    try:
        existing_user = db.users.find_one({"email": user.email})
        if not existing_user or not verify_password(user.password, existing_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {
            "status": "success", 
            "message": "Login successful",
            "code": 200
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
