from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Iterable, Sequence

POSITIVE_WORDS = {
    "love",
    "like",
    "enjoy",
    "great",
    "excited",
    "curious",
    "appreciate",
    "thank",
    "hope",
    "wonder",
}
NEGATIVE_WORDS = {"hate", "annoyed", "angry", "sad", "upset", "worried"}
PLAYFUL_MARKERS = {"haha", "lol", "😂", ";)", "play", "game"}
OPENERS = {"what", "how", "why", "when", "where"}


@dataclass(slots=True)
class ConversationMetrics:
    question_ratio: float
    turn_balance: float
    sentiment_balance: float
    avg_response_seconds: float
    curiosity_score: float
    word_playfulness: float


def _safe_mean(values: Iterable[float]) -> float:
    data = list(values)
    return mean(data) if data else 0.0


def question_ratio(messages: Sequence[str]) -> float:
    if not messages:
        return 0.0
    questions = sum(1 for msg in messages if "?" in msg)
    return questions / len(messages)


def sentiment_balance(messages: Sequence[str]) -> float:
    if not messages:
        return 0.0
    counts = Counter()
    for msg in messages:
        lowered = msg.lower()
        if any(word in lowered for word in POSITIVE_WORDS):
            counts["pos"] += 1
        if any(word in lowered for word in NEGATIVE_WORDS):
            counts["neg"] += 1
    total = counts["pos"] + counts["neg"]
    if total == 0:
        return 0.0
    return (counts["pos"] - counts["neg"]) / total


def curiosity_score(messages: Sequence[str]) -> float:
    if not messages:
        return 0.0
    scores = 0.0
    for msg in messages:
        words = msg.lower().split()
        if words and words[0] in OPENERS:
            scores += 1.0
        if msg.strip().endswith("?"):
            scores += 0.5
    return scores / len(messages)


def word_playfulness(messages: Sequence[str]) -> float:
    if not messages:
        return 0.0
    playful = sum(1 for msg in messages if any(tag in msg.lower() for tag in PLAYFUL_MARKERS))
    return playful / len(messages)


def turn_balance(participant_counts: Sequence[int]) -> float:
    if not participant_counts:
        return 0.0
    total = sum(participant_counts)
    if total == 0:
        return 0.0
    ideal = total / len(participant_counts)
    diffs = [abs(count - ideal) / ideal if ideal else 0 for count in participant_counts]
    return 1 - _safe_mean(diffs)


def average_response_delta(timestamps: Sequence[datetime]) -> float:
    if len(timestamps) < 2:
        return 0.0
    deltas = [
        (t2 - t1).total_seconds()
        for t1, t2 in zip(timestamps[:-1], timestamps[1:])
        if t2 > t1
    ]
    return _safe_mean(deltas)


def compute_metrics(
    user_messages: Sequence[str],
    partner_messages: Sequence[str],
    timestamps: Sequence[datetime],
) -> ConversationMetrics:
    return ConversationMetrics(
        question_ratio=question_ratio(user_messages),
        turn_balance=turn_balance([len(user_messages), len(partner_messages)]),
        sentiment_balance=sentiment_balance(user_messages),
        avg_response_seconds=average_response_delta(timestamps),
        curiosity_score=curiosity_score(user_messages),
        word_playfulness=word_playfulness(user_messages),
    )
