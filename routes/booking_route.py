from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.jwt_handler import decode_access_token
from config.database import db
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
booking_route = APIRouter()

@booking_route.get("/my-flights")
async def get_my_flights(token: str = Depends(oauth2_scheme)):
    try:
        # Verify the token and get user UUID
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_uuid = payload.get("sub")
        if not user_uuid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Find all bookings for this user
        bookings = list(db.bookings.find(
            {"user_uuid": user_uuid},
            {"_id": 0}  # Exclude MongoDB _id from results
        ))

        if not bookings:
            return {
                "message": "You don't have any flight bookings yet.",
                "bookings": []
            }

        # Format the bookings for response
        formatted_bookings = []
        for booking in bookings:
            formatted_bookings.append({
                "passenger_name": booking["passenger_name"],
                "flight_number": booking["flight_number"],
                "seat_number": booking["seat_number"],
                "confirmation_number": booking["confirmation_number"],
                "booking_date": booking["booking_date"].isoformat() if isinstance(booking["booking_date"], datetime) else booking["booking_date"]
            })

        return {
            "message": "Your flight bookings retrieved successfully",
            "bookings": formatted_bookings
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 