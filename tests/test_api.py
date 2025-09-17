from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from resonance.api import ResonanceAPI
from resonance.service import ResonanceService
from resonance.storage import Storage


@pytest.fixture()
def api() -> ResonanceAPI:
    storage = Storage(":memory:")
    service = ResonanceService(storage)
    api_instance = ResonanceAPI(service)
    yield api_instance
    storage.close()


def _post(api: ResonanceAPI, path: str, body: dict) -> dict:
    response = api.handle("POST", path, body=body)
    assert response.status in {200, 201}, response.body
    return response.body


def _get(api: ResonanceAPI, path: str, *, query: dict | None = None) -> dict | list:
    response = api.handle("GET", path, query=query)
    assert response.status == 200, response.body
    return response.body


def test_full_matching_flow(api: ResonanceAPI) -> None:
    first = _post(
        api,
        "/users",
        {
            "email": "one@example.com",
            "display_name": "One",
            "consents": [{"scope": "in_app_analysis", "granted": True}],
        },
    )
    second = _post(
        api,
        "/users",
        {
            "email": "two@example.com",
            "display_name": "Two",
            "consents": [{"scope": "in_app_analysis", "granted": True}],
        },
    )

    base_time = datetime.utcnow()
    conversation = {
        "messages": [
            {
                "author": "self",
                "text": "What futures excite you?",
                "timestamp": base_time.isoformat(),
            },
            {
                "author": "partner",
                "text": "Ones we build together.",
                "timestamp": (base_time + timedelta(seconds=5)).isoformat(),
            },
        ]
    }
    _post(api, f"/users/{first['id']}/conversations", conversation)

    mirror = {
        "messages": [
            {
                "author": "self",
                "text": "Shared futures are powerful.",
                "timestamp": base_time.isoformat(),
            },
            {
                "author": "partner",
                "text": "Absolutely—alignment matters.",
                "timestamp": (base_time + timedelta(seconds=7)).isoformat(),
            },
        ]
    }
    _post(api, f"/users/{second['id']}/conversations", mirror)

    matches = _get(api, f"/users/{first['id']}/matches")
    assert isinstance(matches, list)
    assert matches and matches[0]["user_id"] == second["id"]
    assert 0 < matches[0]["score"] <= 1

    feedback_payload = {
        "user_id": first["id"],
        "partner_id": second["id"],
        "flow_rating": 4,
    }
    _post(api, "/feedback", feedback_payload)

    feedback = _get(api, f"/users/{first['id']}/feedback")
    assert isinstance(feedback, list)
    assert feedback[0]["flow_rating"] == 4


def test_conversation_requires_consent(api: ResonanceAPI) -> None:
    user = _post(api, "/users", {"email": "no@example.com", "display_name": None, "consents": []})
    response = api.handle(
        "POST",
        f"/users/{user['id']}/conversations",
        body={
            "messages": [
                {
                    "author": "self",
                    "text": "Hello",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ]
        },
    )
    assert response.status == 403
    assert "consent" in response.body["detail"].lower()


def test_update_consents_round_trip(api: ResonanceAPI) -> None:
    user = _post(api, "/users", {"email": "scope@example.com", "display_name": "Scope", "consents": []})
    update_response = api.handle(
        "PATCH",
        f"/users/{user['id']}/consents",
        body=[{"scope": "in_app_analysis", "granted": True}],
    )
    assert update_response.status == 200
    consents = {entry["scope"]: entry["granted"] for entry in update_response.body}
    assert consents["in_app_analysis"] is True
