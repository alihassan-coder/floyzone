from openai import AsyncOpenAI
from fastapi import Depends
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from pydantic import BaseModel
from config.database import db
from utils.auth import get_current_user_uuid
from datetime import datetime
import os

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# OpenAI-compatible Gemini client
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Shared context for conversation state
class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None



# Booking Tool
@function_tool
async def book_seat_tool(
    passenger_name: str,
    flight_number: str,
    seat_number: str,
) -> str:
    """
    Book a flight seat for the passenger.
    
    Args:
        passenger_name (str): Name of the passenger.
        flight_number (str): Flight number to book.
        seat_number (str): Seat number to book.
    
    Returns:
        str: Confirmation number for the booking.
    """
    print("+++++++++++")
    print("book seat tool running")
    print(f"Passenger: {passenger_name}, Flight: {flight_number}, Seat: {seat_number}")
    print("+++++++++++")
    try:
        # Get the current user's UUID from the token
        user_uuid = await get_current_user_uuid()
        
        # Simulate booking logic
        confirmation_number = f"CONF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.bookings.insert_one({
            "passenger_name": passenger_name,
            "flight_number": flight_number,
            "seat_number": seat_number,
            "confirmation_number": confirmation_number,
            "user_uuid": user_uuid,
            "booking_date": datetime.now()
        })
        print(f"Booking confirmed for {passenger_name} on flight {flight_number}, seat {seat_number}. Confirmation number: {confirmation_number}")
        print("+++++++++++")
        return confirmation_number
    except Exception as e:
        print("Error in book_seat_tool:", str(e))
        print("+++++++++++")
        return f"Booking failed due to error: {str(e)}"

@function_tool
def faq_lookup_tool(question: str) -> str:
    """
    Look up the answer to a frequently asked question.
    
    Args:
        question (str): The question to look up.
    
    Returns:
        str: The answer to the question.
    """
    print("+++++++++++")
    print("FAQ lookup tool running")
    print(f"Question: {question}")
    print("+++++++++++")
    
    # Simulate FAQ lookup logic
    faq_data = {
        "baggage policy": "FlyZone allows 1 free checked bag and 1 carry-on bag per passenger.",
        "flight status": "You can check flight status on our website or app.",
        "refund rules": "Refunds are available within 24 hours of booking, subject to a fee.",
        "seat selection": "You can select your seat during booking or later through our website.",
        "cancellation policy": "Cancellations are allowed up to 2 hours before departure with a fee.",
        "customer service": "You can reach customer service at 1-800-FLY-ZONE or through our website.",
        "check-in process": "Check-in opens 24 hours before your flight and can be done online or at the airport.",
        "boarding pass": "You can print your boarding pass at home or get it at the airport check-in counter.",
        "flight change": "You can change your flight up to 2 hours before departure for a fee.",
        "luggage weight limit": "The maximum weight for checked luggage is 50 lbs (23 kg).",
        "special assistance": "For special assistance requests, please contact our customer service at least 48 hours before your flight.",
        "pet policy": "Pets are allowed in the cabin for a fee, subject to size and weight restrictions.",
        "meal options": "We offer vegetarian, vegan, and gluten-free meal options on request.",
        "in-flight entertainment": "In-flight entertainment is available on most flights, including movies and music.",
        "wifi availability": "Free wifi is available on all flights, but streaming may be limited.",
        "loyalty program": "Join our FlyZone Loyalty Program to earn points for every flight and enjoy exclusive benefits.",
        "flight cancellation": "If your flight is canceled, you can rebook for free or request a full refund.",
        "boarding time": "Boarding usually starts 30 minutes before departure, so please arrive early.",
        "check-in deadline": "The check-in deadline is 1 hour before departure for domestic flights and 2 hours for international flights.",
    }
    
    answer = faq_data.get(question.lower(), "Sorry, I don't have an answer for that question.")
    print(f"Answer found: {answer}")
    print("+++++++++++")
    return answer
    

@function_tool
async def get_user_bookings_tool() -> str:
    """
    Get all flight bookings for the current user.
    
    Returns:
        str: List of user's bookings with details.
    """
    print("+++++++++++")
    print("get user bookings tool running")
    print("+++++++++++")
    try:
        # Get the current user's UUID from the token
        user_uuid = await get_current_user_uuid()
        
        # Fetch all bookings for the user
        bookings = list(db.bookings.find({"user_uuid": user_uuid}))
        
        if not bookings:
            return "You don't have any flight bookings yet."
        
        # Format the bookings into a readable string
        booking_details = []
        for booking in bookings:
            booking_details.append(
                f"Flight: {booking['flight_number']}, "
                f"Passenger: {booking['passenger_name']}, "
                f"Seat: {booking['seat_number']}, "
                f"Confirmation: {booking['confirmation_number']}"
            )
        
        return "Your bookings:\n" + "\n".join(booking_details)
    except Exception as e:
        print("Error in get_user_bookings_tool:", str(e))
        print("+++++++++++")
        return f"Failed to fetch bookings due to error: {str(e)}"

# Booking Agent
booking_agent = Agent[AirlineAgentContext](
    name="Booking_Agent",
    handoff_description=(
        "Responsible for handling flight bookings. "
        "Collects necessary booking information from the user and completes the reservation process."
    ),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the flight booking agent for FlyZone. Your job is to collect the required details and confirm the booking using the provided tool.
** If the user's request is not related to booking hand off the conversation back to the main_agent

Follow these guidelines:
- Politely collect `only once` the required information: passenger name, flight number, and seat number.
- Do **not** repeat questions for the same missing information.
- Once you have all the required details, **immediately use the `book_seat_tool`** to complete the booking.
- Do **not** ask for user confirmation again after receiving all details — simply process the booking.
- After booking, return the confirmation number clearly and thank the user.

Keep the interaction smooth, efficient, and user-friendly.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[book_seat_tool],
)


faq_agent = Agent(
    name="Faq_agent",
    handoff_description=(
        "Handles general questions about FlyZone Airline, such as baggage policies, flight status, and refund rules. "
        "Provides accurate and helpful information to the user."
    ),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}

# Routine
    1. Identify the last question asked by the customer.
    2. If the question is about checking their own bookings, use the get_user_bookings_tool.
    3. For other questions, use the faq lookup tool to answer the question. Do not rely on your own knowledge.
    4. If you cannot answer the question, transfer back to the triage agent.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[faq_lookup_tool, get_user_bookings_tool]
)


# Main Agent
main_agent = Agent[AirlineAgentContext](
    name="FlyZone_Main_Agent",
    handoff_description=(
        "You are the primary triage agent for FlyZone Airline. "
        "Your responsibility is to understand the customer's request and delegate it to the correct specialized agent. "
        "Transfer booking-related queries to the booking agent and general questions to the FAQ agent."
    ),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a smart and helpful triage agent for FlyZone Airline. Your job is to correctly understand the user's intent and route the query to the appropriate specialized agent.

Guidelines:
- If the user wants to book a flight, reserve a seat, or check booking availability, transfer control to the `booking_agent`.
- If the user is asking a general question** (e.g., about baggage policy, flight status, or refund rules), transfer control to the `faq_agent`.

Make sure you:
- Fully understand the user's intent before handing off.
- Do not respond directly — always delegate to the proper agent based on the request type.
- Follow these rules strictly for correct delegation.
"""
,

    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[booking_agent, faq_agent]
)

booking_agent.handoffs.append(main_agent)
faq_agent.handoffs.append(main_agent)

async def ask_agent(query :str):
    result = await Runner.run(main_agent , query)
    return result.final_output

# # Final function to ask the agent
# async def ask_agent(query: str, current_user: dict):
#     print("+++++++++++")
#     print("Agent running: Processing user query")
#     print(f"Query: {query}")
#     print("+++++++++++")
#     try:
#         user = db.users.find_one({"email": current_user.get("sub")})
#         print(f"Current user in ask_agent: {current_user} | UUID: {user.get('uuid') if user else 'Not found'}")
#         print("+++++++++++")
#         result = await Runner.run(main_agent, query, context=current_user)
#         print("Agent finished processing query.")
#         print("+++++++++++")
#         return result.final_output
#     except Exception as e:
#         print("Error in ask_agent:", str(e))
#         print("+++++++++++")
#         return f"Agent failed due to error: {str(e)}"
