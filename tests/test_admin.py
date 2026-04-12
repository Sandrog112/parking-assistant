from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from parking_assistant.graph.state import ParkingState


def _mock_guardrails_input(state):
    return {"blocked": False}


def _mock_classify_reservation(state):
    return {
        "intent": "reservation",
        "reservation_data": {
            "name": "John",
            "surname": "Doe",
            "car_number": "TEST-123",
            "start_time": "2026-04-12T09:00:00",
            "end_time": "2026-04-12T17:00:00",
        },
    }


def _build_test_graph():
    from parking_assistant.agents.admin import admin_approval_node
    from parking_assistant.graph.workflow import (
        create_reservation_node,
        notify_rejected_node,
        persist_reservation_node,
        route_after_approval,
        route_after_classify,
        route_after_guardrails,
    )

    g = StateGraph(ParkingState)
    g.add_node("guardrails_input", _mock_guardrails_input)
    g.add_node("classify", _mock_classify_reservation)
    g.add_node("create_reservation", create_reservation_node)
    g.add_node("admin_approval", admin_approval_node)
    g.add_node("persist_reservation", persist_reservation_node)
    g.add_node("notify_rejected", notify_rejected_node)

    g.add_edge(START, "guardrails_input")
    g.add_conditional_edges("guardrails_input", route_after_guardrails, {END: END, "classify": "classify"})
    g.add_conditional_edges("classify", route_after_classify, {"chatbot": END, "create_reservation": "create_reservation"})
    g.add_edge("create_reservation", "admin_approval")
    g.add_conditional_edges("admin_approval", route_after_approval, {"persist_reservation": "persist_reservation", "notify_rejected": "notify_rejected"})
    g.add_edge("persist_reservation", END)
    g.add_edge("notify_rejected", END)

    return g.compile(checkpointer=MemorySaver())


@patch("parking_assistant.graph.workflow.httpx")
def test_admin_approval_flow(mock_httpx):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "test1234", "status": "approved"}
    mock_httpx.post.return_value = mock_response

    graph = _build_test_graph()
    config = {"configurable": {"thread_id": "test-approval-1"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="I want to reserve a spot")]},
        config=config,
    )

    state = graph.get_state(config)
    assert state.next == ("admin_approval",)

    result = graph.invoke(
        Command(resume={"approved": True, "reason": "Approved"}),
        config=config,
    )

    messages = result.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    assert "approved" in last_msg.lower() or "confirmed" in last_msg.lower()


def test_admin_rejection_flow():
    graph = _build_test_graph()
    config = {"configurable": {"thread_id": "test-rejection-1"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="I want to reserve a spot")]},
        config=config,
    )

    state = graph.get_state(config)
    assert state.next == ("admin_approval",)

    result = graph.invoke(
        Command(resume={"approved": False, "reason": "No spots available"}),
        config=config,
    )

    messages = result.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    assert "not approved" in last_msg.lower()
    assert "No spots available" in last_msg
