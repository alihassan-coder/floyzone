from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from pydantic import BaseModel
from config.database import db
import os

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# get the cruent login user from the database and print


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

# Booking Tool
@function_tool(
    name_override="book_seat_tool",
    description_override="Books a seat for a passenger on a flight."
)
async def book_seat_tool(
    passenger_name: str,
    seat_number: str,
    flight_number: str
) -> str:
    confirmation_number = f"FZ{hash(passenger_name + seat_number + flight_number) % 10000}"
    return (
        f"Seat {seat_number} has been booked on flight {flight_number} for {passenger_name}. "
        f"Your confirmation number is {confirmation_number}."
    )

# Booking Agent
booking_agent = Agent[AirlineAgentContext](
    name="Booking Agent",
    handoff_description="Handles booking of flights.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the booking agent for FlyZone.
Ask the customer for missing info: passenger name, flight number, and seat number.
Use the booking tool once you have all required info.
You can use the conversation history to understand previous responses.
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
