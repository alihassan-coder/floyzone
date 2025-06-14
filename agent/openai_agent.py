from openai import AsyncOpenAI
from fastapi import Depends
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from pydantic import BaseModel
from config.database import db
from utils.auth import get_current_user_uuid , get_current_user
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
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None



def get_my_uuid(current_user: dict = Depends(get_current_user)):
    uuid = get_current_user_uuid(current_user)
    return {"uuid": uuid}

# Booking Tool
@function_tool
def book_seat_tool(
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
    # Simulate booking logic
    confirmation_number = f"CONF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    
    db.bookings.insert_one({
        "passenger_name": passenger_name,
        "flight_number": flight_number,
        "seat_number": seat_number,
        "confirmation_number": confirmation_number,
        "uuid": get_my_uuid(),
    })
    # Log the booking details
    print(f"Booking confirmed for {passenger_name} on flight {flight_number}, seat {seat_number}. Confirmation number: {confirmation_number}")
    return confirmation_number
    # add booking details to the database with uuid






# Booking Agent
booking_agent = Agent[AirlineAgentContext](
    name="Booking Agent",
    handoff_description="Handles booking of flights.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the booking agent for FlyZone.
Ask the customer only once for missing info: passenger name, flight number, or seat number.
Once you have all info, use the book_seat_tool and return the confirmation number.
Avoid asking for the same detail more than once.
when user provides all details, confirm the booking you not ask for confirmation again only book seat.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[book_seat_tool],
)

# FAQ Agent
faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    handoff_description="Answers questions about FlyZone airline policies.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an FAQ agent.
Answer questions about FlyZone airline policies from this knowledge base:
   FlyZone is a modern global airline based in Dubai, UAE, serving over 90 cities worldwide with a fleet of 120+ aircraft including Boeing 787s and Airbus A350s. Whether you're a first-time flyer or a frequent traveler, FlyZone offers seamless booking, 24/7 customer support, and multilingual AI-powered assistants to answer your questions. Choose from Economy, Business, or Elite First Class—each with reclining seats, USB charging, and HD entertainment. Back seats in Economy include extra legroom rows, and Business/First offer full-flat beds, lounge access, and luxury kits. Enjoy halal-certified meals, vegetarian options, and kids’ menus, all freshly prepared. Every passenger gets 10–40kg baggage allowance, free hand-carry, and real-time flight tracking. Join our SkyFly Rewards to earn miles for upgrades and discounts. FlyZone’s mobile app supports e-boarding passes, seat selection, and live chat help. Safety, comfort, and innovation—FlyZone is your sky companion.

get answers to questions like:
   query: what is the baggage allowance for FlyZone?
   answer: FlyZone offers a baggage allowance of 10–40kg depending on the class of service. Each passenger is also allowed free hand-carry luggage and real-time flight tracking.
    query: what are the meal options on FlyZone flights?
    answer: FlyZone provides halal-certified meals, vegetarian options, and kids’ menus, all freshly prepared for your journey.

Note: If the question is not answered in the knowledge base, politely say you don't have that information contect the customer support.
-make sure the answer is concise and relevant to the question and detail 
-and avoid asking for the same detail more than once.
-if you have ans to the question, provide it directly without asking for confirmation.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)

# Main Agent
main_agent = Agent[AirlineAgentContext](
    name="FlyZone Main Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the FlyZone main assistant.
Route queries to the FAQ or Booking agent based on content.
If the query is unsupported, politely say so.
Use conversation history for better understanding.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[faq_agent, booking_agent],
)

# Setup bi-directional handoffs
faq_agent.handoffs.append(main_agent)
booking_agent.handoffs.append(main_agent)

# Final function to ask the agent
async def ask_agent(query: str, current_user: dict):
    try:
        user = db.users.find_one({"email": current_user.get("sub")})
        print(f"Current user in ask_agent: {current_user} | UUID: {user.get('uuid') if user else 'Not found'}")
        result = await Runner.run(main_agent, query, context=current_user)
        return result.final_output
    except Exception as e:
        return f"Agent failed due to error: {str(e)}"
