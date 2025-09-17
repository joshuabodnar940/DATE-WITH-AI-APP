from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from resonance.models import ConsentScope
from resonance.service import ConversationMessage, ResonanceService
from resonance.storage import Storage


@pytest.fixture()
def service(tmp_path):
    db_path = tmp_path / "resonance.db"
    storage = Storage(db_path)
    svc = ResonanceService(storage)
    yield svc
    storage.close()


def create_sample_conversation(start: datetime, delta: float) -> list[ConversationMessage]:
    return [
        ConversationMessage(author="self", text="What lights you up?", timestamp=start),
        ConversationMessage(
            author="partner",
            text="I love designing playful futures!",
            timestamp=start + timedelta(seconds=delta),
        ),
        ConversationMessage(
            author="self",
            text="Haha same, I appreciate curious minds.",
            timestamp=start + timedelta(seconds=delta * 2),
        ),
    ]


def test_end_to_end_matching(service: ResonanceService):
    user_a = service.register_user(
        "a@example.com",
        "Alice",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: True},
    )
    user_b = service.register_user(
        "b@example.com",
        "Bob",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: True},
    )
    user_c = service.register_user(
        "c@example.com",
        "Charlie",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: True},
    )

    now = datetime.utcnow()
    service.ingest_conversation(user_a.id, create_sample_conversation(now, 4))
    service.ingest_conversation(user_b.id, create_sample_conversation(now + timedelta(seconds=30), 5))
    service.ingest_conversation(user_c.id, create_sample_conversation(now + timedelta(seconds=60), 15))

    matches = service.suggest_matches(user_a.id, limit=2)
    assert len(matches) == 2
    assert matches[0].user_id in {user_b.id, user_c.id}
    assert matches[0].score >= matches[1].score


def test_consent_required(service: ResonanceService):
    user = service.register_user(
        "d@example.com",
        "Dana",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: False},
    )
    with pytest.raises(PermissionError):
        service.ingest_conversation(
            user.id,
            [
                ConversationMessage(
                    author="self",
                    text="hello?",
                    timestamp=datetime.utcnow(),
                )
            ],
        )


def test_feedback_cycle(service: ResonanceService):
    user_a = service.register_user(
        "alpha@example.com",
        "Alpha",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: True},
    )
    user_b = service.register_user(
        "beta@example.com",
        "Beta",
        consent_flags={ConsentScope.IN_APP_ANALYSIS: True},
    )
    feedback = service.submit_feedback(user_a.id, user_b.id, flow_rating=4)
    assert feedback.flow_rating == 4
    history = service.list_feedback(user_a.id)
    assert len(history) == 1
    assert history[0].partner_id == user_b.id
