from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from typing import List, Sequence

from .analytics import compute_metrics
from .models import (
    ChemistryProfile,
    ConsentDecision,
    ConsentScope,
    MatchCandidate,
    MatchFeedback,
    User,
)
from .storage import Storage


@dataclass(slots=True)
class ConversationMessage:
    """Message submitted for conversational analysis."""

    author: str
    text: str
    timestamp: datetime

    def __post_init__(self) -> None:
        if self.author not in {"self", "partner"}:
            raise ValueError("author must be 'self' or 'partner'")
        if not self.text.strip():
            raise ValueError("message text cannot be empty")


class ResonanceService:
    """High-level orchestration of consent, analytics, and matching."""

    def __init__(self, storage: Storage | None = None) -> None:
        self.storage = storage or Storage(":memory:")

    # -- user onboarding -------------------------------------------------
    def register_user(
        self,
        email: str,
        display_name: str | None,
        *,
        consent_flags: dict[ConsentScope, bool] | None = None,
    ) -> User:
        try:
            user = self.storage.add_user(email=email, display_name=display_name)
        except Exception as exc:  # pragma: no cover - sqlite raises sqlite3.IntegrityError
            raise ValueError("email already registered") from exc
        flags = consent_flags or {}
        for scope in ConsentScope:
            granted = bool(flags.get(scope, False))
            self.storage.set_consent(user.id, scope, granted)
        return user

    def get_user(self, user_id: int) -> User:
        user = self.storage.get_user(user_id)
        if not user:
            raise ValueError("user not found")
        return user

    def get_consents(self, user_id: int) -> dict[ConsentScope, ConsentDecision]:
        if not self.storage.get_user(user_id):
            raise ValueError("user not found")
        consents = self.storage.get_consents(user_id)
        for scope in ConsentScope:
            consents.setdefault(
                scope,
                ConsentDecision(user_id=user_id, scope=scope, granted=False),
            )
        return consents

    def update_consents(self, user_id: int, flags: dict[ConsentScope, bool]) -> dict[ConsentScope, ConsentDecision]:
        if not self.storage.get_user(user_id):
            raise ValueError("user not found")
        for scope, granted in flags.items():
            self.storage.set_consent(user_id, scope, bool(granted))
        return self.get_consents(user_id)

    # -- conversation analysis ------------------------------------------
    def ingest_conversation(
        self, user_id: int, messages: Sequence[ConversationMessage]
    ) -> ChemistryProfile:
        if not messages:
            raise ValueError("no messages provided")
        if not self.storage.get_user(user_id):
            raise ValueError("user not found")
        consents = self.get_consents(user_id)
        if not consents[ConsentScope.IN_APP_ANALYSIS].granted:
            raise PermissionError("in-app analysis consent required")

        ordered = sorted(messages, key=lambda msg: msg.timestamp)
        user_messages = [msg.text for msg in ordered if msg.author == "self"]
        partner_messages = [msg.text for msg in ordered if msg.author == "partner"]
        timestamps = [msg.timestamp for msg in ordered]

        metrics = compute_metrics(user_messages, partner_messages, timestamps)
        profile = ChemistryProfile(
            user_id=user_id,
            question_ratio=metrics.question_ratio,
            turn_balance=metrics.turn_balance,
            sentiment_balance=metrics.sentiment_balance,
            avg_response_seconds=metrics.avg_response_seconds,
            curiosity_score=metrics.curiosity_score,
            word_playfulness=metrics.word_playfulness,
            updated_at=datetime.utcnow(),
        )
        return self.storage.upsert_profile(profile)

    # -- matching --------------------------------------------------------
    def suggest_matches(self, user_id: int, limit: int = 3) -> List[MatchCandidate]:
        profile = self.storage.get_profile(user_id)
        if not profile:
            raise ValueError("no chemistry profile for user")
        user_vector = list(profile.as_vector().values())
        candidates: List[MatchCandidate] = []
        for other_profile in self.storage.iter_profiles(exclude_user=user_id):
            other_vector = list(other_profile.as_vector().values())
            score = self._score(user_vector, other_vector)
            alignment = self._alignment(profile, other_profile)
            candidates.append(MatchCandidate(user_id=other_profile.user_id, score=score, alignment=alignment))
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[: max(limit, 0)]

    def _score(self, left: Sequence[float], right: Sequence[float]) -> float:
        distance = sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))
        return round(1 / (1 + distance), 4)

    def _alignment(self, base: ChemistryProfile, other: ChemistryProfile) -> dict[str, float]:
        alignment: dict[str, float] = {}
        for key in base.as_vector():
            base_value = base.as_vector()[key]
            other_value = other.as_vector()[key]
            alignment[key] = round(max(0.0, 1 - abs(base_value - other_value)), 3)
        return alignment

    # -- feedback --------------------------------------------------------
    def submit_feedback(self, user_id: int, partner_id: int, flow_rating: int) -> MatchFeedback:
        if user_id == partner_id:
            raise ValueError("cannot submit feedback for self")
        if not 1 <= flow_rating <= 5:
            raise ValueError("flow rating must be between 1 and 5")
        if not self.storage.get_user(user_id) or not self.storage.get_user(partner_id):
            raise ValueError("user not found")
        return self.storage.add_feedback(user_id, partner_id, flow_rating)

    def list_feedback(self, user_id: int) -> List[MatchFeedback]:
        if not self.storage.get_user(user_id):
            raise ValueError("user not found")
        return self.storage.list_feedback(user_id)
