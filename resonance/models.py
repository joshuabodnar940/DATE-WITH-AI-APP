from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ConsentScope(str, Enum):
    """Scopes of consent supported by the system."""

    IN_APP_ANALYSIS = "in_app_analysis"
    SOCIAL_SCRAPE = "social_scrape"
    VOICE_ANALYSIS = "voice_analysis"


@dataclass(slots=True)
class User:
    id: int
    email: str
    display_name: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ConsentDecision:
    user_id: int
    scope: ConsentScope
    granted: bool
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ChemistryProfile:
    user_id: int
    question_ratio: float
    turn_balance: float
    sentiment_balance: float
    avg_response_seconds: float
    curiosity_score: float
    word_playfulness: float
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def as_vector(self) -> Dict[str, float]:
        return {
            "question_ratio": self.question_ratio,
            "turn_balance": self.turn_balance,
            "sentiment_balance": self.sentiment_balance,
            "avg_response_seconds": self.avg_response_seconds,
            "curiosity_score": self.curiosity_score,
            "word_playfulness": self.word_playfulness,
        }


@dataclass(slots=True)
class MatchCandidate:
    user_id: int
    score: float
    alignment: Dict[str, float]


@dataclass(slots=True)
class MatchFeedback:
    id: int
    user_id: int
    partner_id: int
    flow_rating: int
    created_at: datetime = field(default_factory=datetime.utcnow)
