from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ReservationRequest(BaseModel):
    name: str
    surname: str
    car_number: str
    start_time: str
    end_time: str


class Reservation(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    name: str
    surname: str
    car_number: str
    start_time: str
    end_time: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ApprovalDecision(BaseModel):
    reservation_id: str
    approved: bool
    reason: str = ""
