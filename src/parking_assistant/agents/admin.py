from langgraph.types import interrupt


def admin_approval_node(state: dict) -> dict:
    pending = state.get("pending_reservation", {})

    decision = interrupt({
        "type": "approval_request",
        "reservation": pending,
        "message": f"Approve reservation for {pending.get('name', '')} {pending.get('surname', '')}? "
                   f"Car: {pending.get('car_number', '')}, "
                   f"Period: {pending.get('start_time', '')} to {pending.get('end_time', '')}",
    })

    return {
        "approval": {
            "approved": decision.get("approved", False),
            "reason": decision.get("reason", ""),
        }
    }
