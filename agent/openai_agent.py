from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool,RunContextWrapper , handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from pydantic import BaseModel
from config.database import db
import os

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# OpenAI-compatible Gemini client
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Shared context
class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None



# FAQ Tool
@function_tool(
    name_override="faq_lookup_tool",
    description_override="Lookup frequently asked questions about the airline."
)
async def faq_lookup_tool(question: str) -> str:
    if "bag" in question or "baggage" in question:
        return "You are allowed to bring one bag on the plane. It must be under 50 pounds and 22x14x9 inches."
    elif "seats" in question or "plane" in question:
        return (
            "There are 120 seats on the plane. "
            "22 business class seats, 98 economy. "
            "Exit rows: 4 and 16. Economy Plus: Rows 5-8."
        )
    elif "wifi" in question.lower():
        return "We have free wifi on the plane. Join Airline-Wifi."
    return "Sorry, I don't know the answer to that question."



# A function that gets the current user's UUID from the database
def get_current_user_uuid(current_user: dict) -> str | None:
    """
    Get the current user's UUID from the database using their email.
    """
    user = db.users.find_one({"email": current_user.get("sub")})
    if user:
        return user.get("uuid")
    return None


# Booking Tool
@function_tool
def book_seat_tool(
    context: RunContextWrapper,
    passenger_name: str,
    flight_number: str,
    seat_number: str,
) -> str:
    """
    Arguments:
    - passenger_name: Name of the passenger booking the flight.
    - flight_number: Flight number to book.
    - seat_number: Seat number to book.
    Returns:
    - Confirmation message with a unique confirmation number.
    Example:
    query : i want to book a flight for John Doe on flight 1234 in seat 12A
    response: "Booking confirmed! Your confirmation number is CONF-JOH-1234-12A."
    """

    current_user = context.current_user if context else {}

    # Get UUID from the database
    user_uuid = get_current_user_uuid(current_user)

    # Simulate booking logic
    confirmation_number = f"CONF-{passenger_name[:3].upper()}-{flight_number}-{seat_number}"

    # Update the database with booking info (if needed)
    db.bookings.insert_one({
        "passenger_name": passenger_name,
        "flight_number": flight_number,
        "seat_number": seat_number,
        "confirmation_number": confirmation_number,
        "user_uuid": user_uuid,
    })

    return f"Booking confirmed! Your confirmation number is {confirmation_number}."




# Booking Agent
booking_agent = Agent[AirlineAgentContext](
    name="Booking Agent",
    handoff_description="Handles booking of flights.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the booking agent for FlyZone.
Ask the customer for missing info: passenger name, flight number, and seat number.
Use the booking tool once you have all required info.
You can use the conversation history to understand previous responses.
and make sure to ask for any missing information only one time not again and again.
not ask conferm information again and again,book the seat and return the confirmation number.
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
Use the FAQ lookup tool to answer questions.
If unsure or if the user wants to book, hand off to the main agent.
Use the conversation history to detect booking-related questions.
""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[faq_lookup_tool],
)

# Main Agent
main_agent = Agent[AirlineAgentContext](
    name="FlyZone Main Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the FlyZone main assistant.
Route the query to either the FAQ agent or Booking agent based on content.
If the query is unsupported, politely inform the user.
Use the conversation history to better understand context.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[faq_agent, booking_agent],
)

# Setup bi-directional handoffs
faq_agent.handoffs.append(main_agent)
booking_agent.handoffs.append(main_agent)

conversation_history = []


async def ask_agent(query: str, current_user: dict):
    # Use 'sub' as the email field from JWT
    user = db.users.find_one({"email": current_user.get("sub")})
    if user:
        print(f"Current user in ask_agent: {current_user} | UUID: {user.get('uuid')}")
    else:
        print(f"Current user in ask_agent: {current_user} | UUID: Not found")
    result = await Runner.run(main_agent, query)
    return result.final_output


# # CLI loop with logging
# if __name__ == "__main__":
#     print("🛫 Welcome to FlyZone Assistant. Type 'exit' to leave.")

#     while True:
#         query = input("\n💬 You: ")

#         if query.lower() in {"exit", "quit"}:
#             print("👋 Goodbye!")
#             break

#         # Track user input
#         conversation_history.append({"role": "user", "content": query})

#         print("🔍 Routing through Main Agent...")

#         # Run the conversation with main agent
#         result = Runner.run_sync(main_agent, query)

#         # Track agent output
#         conversation_history.append({"role": "assistant", "content": result.final_output})

#         # Debug: print the actual agent who responded
#         print(f"\n🤖 Agent Responded: {result.final_output}")
#         print("================================================")
#         print(f"📜 input + output of user : {result.to_input_list()}")
#         print("================================================")
#         print(f"all detail : {result.last_agent}")
#         print("================================================")
#         print(f"last agent name  : {result.last_agent.name}")
#         print("====================================================")