from parking_assistant.models import ApprovalDecision, Reservation, ReservationRequest


def test_reservation_request_fields():
    req = ReservationRequest(
        name="Alice",
        surname="Smith",
        car_number="XYZ-9999",
        start_time="2026-04-12T10:00:00",
        end_time="2026-04-12T14:00:00",
    )
    assert req.name == "Alice"
    assert req.car_number == "XYZ-9999"


def test_reservation_defaults():
    res = Reservation(
        name="Bob",
        surname="Jones",
        car_number="DEF-5678",
        start_time="2026-04-12T09:00:00",
        end_time="2026-04-12T17:00:00",
    )
    assert res.status == "pending"
    assert len(res.id) == 8
    assert res.created_at


def test_reservation_from_request(sample_reservation_request):
    res = Reservation(**sample_reservation_request.model_dump())
    assert res.name == sample_reservation_request.name
    assert res.status == "pending"


def test_approval_decision():
    decision = ApprovalDecision(reservation_id="abc12345", approved=True, reason="Looks good")
    assert decision.approved is True
    assert decision.reason == "Looks good"
