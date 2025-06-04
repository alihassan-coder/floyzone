from fastapi import APIRouter, HTTPException
from config.database import db
from validation.user_validation import UserRegister, UserLogin
from utils.hash import hash_password, verify_password
from utils.jwt_handler import create_access_token


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
        
        # Create token
        token_data = {"sub": existing_user["email"]}
        token = create_access_token(token_data)

        return {
            "status": "success", 
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "code": 200
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")