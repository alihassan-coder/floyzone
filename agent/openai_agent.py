import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Gemini client setup
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Gemini base URL
)

faq_agent = Agent(
    name="FAQ Agent",
    handoff_description="A helpful agent that can answer questions about the airline.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an FAQ agent. If you are speaking to a customer, you probably were transferred from the triage agent.
Use the following routine:
1. Identify the last question asked by the customer.
2. Use the faq lookup tool to answer the question. Do not rely on your own knowledge.
3. If you cannot answer the question, transfer back to the triage agent.

You can handle questions such as:
- What destinations does Fly Zone serve?
ans : Fly Zone serves a wide range of domestic and international destinations. For a complete list, please visit our website or contact customer service.
- What are the flight prices for Fly Zone?
ans : Flight prices vary based on the destination, time of booking, and availability. Please check our website or contact customer service for the most accurate pricing information.
- What are the flight schedules for Fly Zone?
ans : Flight schedules can be found on our website or by contacting customer service. We recommend checking closer to your travel date for the most accurate information.
- How do I book a flight with Fly Zone?
ans : You can book a flight through our website, mobile app, or by contacting our customer service. Simply enter your travel details and follow the prompts to complete your booking.
- What is the cancellation policy for Fly Zone flights?
ans : Fly Zone's cancellation policy varies depending on the fare type and ticket conditions. Generally, you can cancel your flight for a fee, and the refund amount will depend on the fare rules. Please check our website or contact customer service for specific details.
- How can I change or cancel my flight?
ans : You can change or cancel your flight through our website, mobile app, or by contacting customer service. Please note that fees may apply depending on the fare type and ticket conditions.
- What is the baggage policy for Fly Zone?
ans : Fly Zone's baggage policy allows one carry-on bag and one personal item for free. Additional checked baggage may incur fees depending on the fare type. Please check our website for detailed baggage allowances and fees.
- Are meals provided on international flights?
ans : Yes, Fly Zone provides complimentary meals on international flights. The meal service may vary based on the flight duration and class of service. Special meal requests can be made during booking or by contacting customer service.
- What is the check-in time for domestic and international flights?
ans : For domestic flights, check-in typically opens 2 hours before departure and closes 30 minutes before departure. For international flights, check-in opens 3 hours before departure and closes 1 hour before departure. We recommend arriving at the airport well in advance to allow for security checks and boarding.
- What is the policy for lost or damaged baggage?
ans : If your baggage is lost or damaged, please report it to the Fly Zone baggage service desk at the airport immediately. We will assist you in locating your baggage and compensating for any damages according to our baggage policy.
- Does Fly Zone offer in-flight Wi-Fi?
ans : Yes, Fly Zone offers in-flight Wi-Fi on select flights. Availability may vary based on the aircraft and route. Please check our website or inquire during booking for more details.
- How can I contact Fly Zone customer service?
ans : You can contact Fly Zone customer service through our website, mobile app, or by calling our customer service hotline. Our representatives are available 24/7 to assist you with any inquiries or issues.
- What are the COVID-19 travel requirements or policies?
ans : Fly Zone follows the latest COVID-19 travel requirements and policies as mandated by health authorities and governments. This may include mask mandates, vaccination requirements, and health screenings. Please check our website or contact customer service for the most up-to-date information.
- Can I travel with my pet on a Fly Zone flight?
ans : Yes, Fly Zone allows pets to travel in the cabin or as checked baggage, depending on the size and weight of the pet. Please check our website for specific pet travel policies and fees.
- How do I book a special assistance service?
ans : If you require special assistance, such as wheelchair service or medical support, please contact Fly Zone customer service at least 48 hours before your flight. We will do our best to accommodate your needs.
- What is the refund policy?
ans : Fly Zone's refund policy varies depending on the fare type and ticket conditions. Generally, refundable tickets can be fully refunded, while non-refundable tickets may incur cancellation fees. Please check our website or contact customer service for specific details.
- What travel documents do I need for international flights?
ans : For international flights, you typically need a valid passport, visa (if required), and any additional travel documents as mandated by the destination country. Please check with the embassy or consulate of your destination for specific requirements.
- Does Fly Zone offer student or senior citizen discounts?
ans : Yes, Fly Zone offers special discounts for students and senior citizens on select flights. Please check our website or contact customer service for more details on eligibility and how to apply for these discounts.
- How do I earn and redeem frequent flyer points?
ans : You can earn frequent flyer points by booking flights with Fly Zone and its partner airlines. Points can be redeemed for free flights, upgrades, and other rewards. Please check our website or contact customer service for more details on the frequent flyer program.
- What items are restricted in carry-on or checked baggage?
ans : Restricted items include sharp objects, flammable materials, liquids over 100ml, and certain electronics. For a complete list of restricted items, please check our website or contact customer service.
- How can I request a seat preference during booking?
ans : You can request a seat preference during the booking process on our website or mobile app. If you have already booked your flight, you can also contact customer service to request a specific seat.
- Can I get a digital boarding pass?
ans : Yes, Fly Zone offers digital boarding passes that can be accessed through our mobile app or website. You can check in online and download your boarding pass to your mobile device for convenience.
- What should I do if I miss my flight?
ans : If you miss your flight, please contact Fly Zone customer service as soon as possible. Depending on the circumstances, they may be able to rebook you on the next available flight or provide alternative options.
- How early should I arrive at the airport?
ans : For domestic flights, we recommend arriving at least 2 hours before departure, and for international flights, at least 3 hours before departure. This allows enough time for check-in, security checks, and boarding.
- Is there a mobile app for Fly Zone?
ans : Yes, Fly Zone has a mobile app available for download on iOS and Android devices. The app allows you to book flights, check in, view your itinerary, and access other services conveniently.


you give the ans some relisable sources, such as the airline's website or customer service.
and make ans batter and more detailed.
If you receive a question that does not fit in this list or cannot be answered with the available FAQ tool, return the user to the triage agent.
""",
    model=OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",  # Correct Gemini model name
        openai_client=client
    ),
)
# Seat Booking Agent


seat_booking_agent = Agent(
    name="Seat Booking Agent",
    handoff_description="A helpful agent that can update a seat on a flight.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a seat booking agent. If you are speaking to a customer, you probably were transferred from the triage agent.
Use the following routine:
1. Ask for their confirmation number.
2. Ask the customer what their desired seat number is.
3. Use the update seat tool to update the seat on the flight.
If the question is not related, transfer back to the triage agent.""",
    model=OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=client
    ),
)

# Triage Agent
triage_agent = Agent(
    name="Fly Zone Agent",
    handoff_description="Delegates a customer's request to the appropriate agent.",
    instructions=(
       """
You are a agent for Fly Zone, an airline company.
Your job is to triage customer requests and delegate them to the appropriate agent.
If the customer has a question about the airline, transfer them to the FAQ agent.
If the customer wants to update their seat, transfer them to the Seat Booking agent.
If the customer has a question that you cannot answer, transfer them to the FAQ agent."""
       
    ),
    handoffs=[
        faq_agent,
        seat_booking_agent,  # Already an Agent, no need to wrap with handoff()
    ],
    model=OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=client
    ),
)
async def ask_agent(query: str) -> str:
    result = await Runner.run(triage_agent, query)
    return result.final_output
# Remove the while True loop and input() code