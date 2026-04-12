import pytest


@pytest.mark.asyncio
async def test_create_reservation(mcp_client):
    response = await mcp_client.post("/reservations", json={
        "name": "John",
        "surname": "Doe",
        "car_number": "ABC-1234",
        "start_time": "2026-04-12T09:00:00",
        "end_time": "2026-04-12T17:00:00",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["name"] == "John"
    assert len(data["id"]) == 8


@pytest.mark.asyncio
async def test_list_reservations(mcp_client):
    await mcp_client.post("/reservations", json={
        "name": "Alice",
        "surname": "Smith",
        "car_number": "XYZ-9999",
        "start_time": "2026-04-12T10:00:00",
        "end_time": "2026-04-12T14:00:00",
    })
    response = await mcp_client.get("/reservations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_approve_reservation(mcp_client):
    create_resp = await mcp_client.post("/reservations", json={
        "name": "Bob",
        "surname": "Jones",
        "car_number": "DEF-5678",
        "start_time": "2026-04-12T08:00:00",
        "end_time": "2026-04-12T12:00:00",
    })
    res_id = create_resp.json()["id"]

    approve_resp = await mcp_client.post(f"/reservations/{res_id}/approve", json={
        "reservation_id": res_id,
        "approved": True,
        "reason": "Approved",
    })
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_reservation(mcp_client):
    create_resp = await mcp_client.post("/reservations", json={
        "name": "Carol",
        "surname": "White",
        "car_number": "GHI-0000",
        "start_time": "2026-04-12T13:00:00",
        "end_time": "2026-04-12T15:00:00",
    })
    res_id = create_resp.json()["id"]

    reject_resp = await mcp_client.post(f"/reservations/{res_id}/approve", json={
        "reservation_id": res_id,
        "approved": False,
        "reason": "No spots available",
    })
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
