from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

from parking_assistant.config import settings
from parking_assistant.rag.retriever import retrieve


class IntentClassification(BaseModel):
    intent: str = Field(description="Either 'info' or 'reservation'")
    name: str = Field(default="", description="User's first name if provided")
    surname: str = Field(default="", description="User's surname if provided")
    car_number: str = Field(default="", description="Car plate number if provided")
    start_time: str = Field(default="", description="Reservation start time if provided")
    end_time: str = Field(default="", description="Reservation end time if provided")


SYSTEM_PROMPT = (
    "You are a helpful parking assistant chatbot. You help users with parking-related "
    "questions such as rates, availability, hours, location, and reservations. "
    "Use the provided context to answer questions accurately. "
    "If a user wants to make a reservation, collect their name, surname, car number, "
    "and desired reservation period. Stay on topic - only discuss parking-related matters."
)

CLASSIFY_PROMPT = (
    "Classify the user's intent. If they want to make or discuss a reservation, "
    "return intent='reservation' and extract any provided details (name, surname, "
    "car_number, start_time, end_time). Otherwise return intent='info'. "
    "Only set fields that the user has explicitly provided."
)


def _get_llm():
    return AzureChatOpenAI(
        azure_deployment=settings.azure_deployment,
        openai_api_key=settings.dial_api_key,
        azure_endpoint=settings.azure_endpoint,
        openai_api_version=settings.api_version,
        temperature=0,
    )


def classify_intent(state: dict) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "info"}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    llm = _get_llm().with_structured_output(IntentClassification)
    result = llm.invoke([
        SystemMessage(content=CLASSIFY_PROMPT),
        last_message,
    ])

    output = {"intent": result.intent}
    if result.intent == "reservation":
        output["reservation_data"] = {
            "name": result.name,
            "surname": result.surname,
            "car_number": result.car_number,
            "start_time": result.start_time,
            "end_time": result.end_time,
        }

    return output


def chatbot_node(state: dict) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [AIMessage(content="Hello! How can I help you with parking today?")]}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    context_docs = retrieve(user_text)
    context_str = "\n\n".join(context_docs) if context_docs else "No specific information found."

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=f"{SYSTEM_PROMPT}\n\nRelevant information:\n{context_str}"),
        *messages,
    ])

    return {"messages": [response], "context": context_docs}
