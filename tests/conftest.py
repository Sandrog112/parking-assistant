import pytest

from parking_assistant.models import Reservation, ReservationRequest


@pytest.fixture
def sample_reservation_request():
    return ReservationRequest(
        name="John",
        surname="Doe",
        car_number="ABC-1234",
        start_time="2026-04-12T09:00:00",
        end_time="2026-04-12T17:00:00",
    )


@pytest.fixture
def sample_reservation():
    return Reservation(
        name="John",
        surname="Doe",
        car_number="ABC-1234",
        start_time="2026-04-12T09:00:00",
        end_time="2026-04-12T17:00:00",
    )


@pytest.fixture
def clean_reservations(tmp_path, monkeypatch):
    test_file = tmp_path / "reservations.json"
    monkeypatch.setattr("parking_assistant.config.settings.reservations_file", str(test_file))
    return test_file


@pytest.fixture
def mcp_client(clean_reservations):
    from httpx import ASGITransport, AsyncClient

    from parking_assistant.mcp.server import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
