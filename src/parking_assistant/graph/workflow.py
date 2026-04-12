import httpx
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from parking_assistant.agents.admin import admin_approval_node
from parking_assistant.agents.chatbot import chatbot_node, classify_intent
from parking_assistant.config import settings
from parking_assistant.graph.state import ParkingState
from parking_assistant.guardrails.filters import guardrails_input_node, guardrails_output_node
from parking_assistant.models import Reservation


def route_after_guardrails(state: ParkingState) -> str:
    if state.get("blocked"):
        return END
    return "classify"


def route_after_classify(state: ParkingState) -> str:
    if state.get("intent") == "reservation":
        return "create_reservation"
    return "chatbot"


def route_after_approval(state: ParkingState) -> str:
    approval = state.get("approval", {})
    if approval.get("approved"):
        return "persist_reservation"
    return "notify_rejected"


def create_reservation_node(state: ParkingState) -> dict:
    data = state.get("reservation_data", {})
    reservation = Reservation(
        name=data.get("name", ""),
        surname=data.get("surname", ""),
        car_number=data.get("car_number", ""),
        start_time=data.get("start_time", ""),
        end_time=data.get("end_time", ""),
    )
    return {
        "pending_reservation": reservation.model_dump(),
        "messages": [AIMessage(
            content=f"Reservation request created (ID: {reservation.id}). "
                    f"Waiting for administrator approval..."
        )],
    }


def persist_reservation_node(state: ParkingState) -> dict:
    pending = state.get("pending_reservation", {})
    try:
        response = httpx.post(
            f"{settings.mcp_server_url}/reservations",
            json={
                "name": pending.get("name", ""),
                "surname": pending.get("surname", ""),
                "car_number": pending.get("car_number", ""),
                "start_time": pending.get("start_time", ""),
                "end_time": pending.get("end_time", ""),
            },
        )
        result = response.json()
        return {
            "messages": [AIMessage(
                content=f"Your reservation has been approved and confirmed! "
                        f"Reservation ID: {result.get('id', pending.get('id', ''))}. "
                        f"Name: {pending.get('name', '')} {pending.get('surname', '')} | "
                        f"Car: {pending.get('car_number', '')} | "
                        f"Period: {pending.get('start_time', '')} to {pending.get('end_time', '')}"
            )]
        }
    except httpx.HTTPError:
        return {
            "messages": [AIMessage(
                content="Your reservation was approved but there was an issue saving it. "
                        "Please contact support."
            )]
        }


def notify_rejected_node(state: ParkingState) -> dict:
    approval = state.get("approval", {})
    reason = approval.get("reason", "No reason provided")
    return {
        "messages": [AIMessage(
            content=f"Your reservation was not approved. Reason: {reason}"
        )]
    }


def build_graph() -> StateGraph:
    g = StateGraph(ParkingState)

    g.add_node("guardrails_input", guardrails_input_node)
    g.add_node("classify", classify_intent)
    g.add_node("chatbot", chatbot_node)
    g.add_node("create_reservation", create_reservation_node)
    g.add_node("admin_approval", admin_approval_node)
    g.add_node("persist_reservation", persist_reservation_node)
    g.add_node("notify_rejected", notify_rejected_node)
    g.add_node("guardrails_output", guardrails_output_node)

    g.add_edge(START, "guardrails_input")
    g.add_conditional_edges("guardrails_input", route_after_guardrails, {END: END, "classify": "classify"})
    g.add_conditional_edges("classify", route_after_classify, {"chatbot": "chatbot", "create_reservation": "create_reservation"})
    g.add_edge("chatbot", "guardrails_output")
    g.add_edge("guardrails_output", END)
    g.add_edge("create_reservation", "admin_approval")
    g.add_conditional_edges("admin_approval", route_after_approval, {"persist_reservation": "persist_reservation", "notify_rejected": "notify_rejected"})
    g.add_edge("persist_reservation", END)
    g.add_edge("notify_rejected", END)

    return g


graph = build_graph().compile(checkpointer=MemorySaver())
