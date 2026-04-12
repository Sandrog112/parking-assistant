from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ParkingState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    context: list[str]
    intent: str
    reservation_data: dict
    pending_reservation: dict
    approval: dict
    blocked: bool
