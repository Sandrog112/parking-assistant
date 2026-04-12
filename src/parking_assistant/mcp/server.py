import json
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException

from parking_assistant.config import settings
from parking_assistant.models import ApprovalDecision, Reservation, ReservationRequest

app = FastAPI(title="Parking Assistant MCP")


def _get_file_path() -> Path:
    return Path(settings.reservations_file)


def _load_reservations() -> list[dict]:
    path = _get_file_path()
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def _save_reservations(reservations: list[dict]) -> None:
    path = _get_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(reservations, f, indent=2)


@app.post("/reservations", response_model=Reservation)
async def create_reservation(req: ReservationRequest):
    reservation = Reservation(**req.model_dump())
    reservations = _load_reservations()
    reservations.append(reservation.model_dump())
    _save_reservations(reservations)
    return reservation


@app.get("/reservations", response_model=list[Reservation])
async def list_reservations():
    return _load_reservations()


@app.get("/reservations/{reservation_id}", response_model=Reservation)
async def get_reservation(reservation_id: str):
    reservations = _load_reservations()
    for r in reservations:
        if r["id"] == reservation_id:
            return r
    raise HTTPException(status_code=404, detail="Reservation not found")


@app.post("/reservations/{reservation_id}/approve", response_model=Reservation)
async def approve_reservation(reservation_id: str, decision: ApprovalDecision):
    reservations = _load_reservations()
    for r in reservations:
        if r["id"] == reservation_id:
            r["status"] = "approved" if decision.approved else "rejected"
            r["approval_time"] = datetime.now(UTC).isoformat()
            r["approval_reason"] = decision.reason
            _save_reservations(reservations)
            return r
    raise HTTPException(status_code=404, detail="Reservation not found")


@app.delete("/reservations/{reservation_id}")
async def cancel_reservation(reservation_id: str):
    reservations = _load_reservations()
    updated = [r for r in reservations if r["id"] != reservation_id]
    if len(updated) == len(reservations):
        raise HTTPException(status_code=404, detail="Reservation not found")
    _save_reservations(updated)
    return {"message": "Reservation cancelled"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
