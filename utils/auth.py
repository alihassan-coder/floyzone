from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from utils.jwt_handler import decode_access_token
from config.database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Token payload invalid")

    user = db.users.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# get current login user uuid 
def get_current_user_uuid(current_user: dict) -> str | None:
    return current_user.get("uuid")