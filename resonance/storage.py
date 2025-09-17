from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .models import (
    ChemistryProfile,
    ConsentDecision,
    ConsentScope,
    MatchFeedback,
    User,
)

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class Storage:
    """SQLite-backed persistence for the Resonance+ prototype."""

    def __init__(self, path: str | Path = "resonance.db") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        self._connection.row_factory = sqlite3.Row
        self.initialise()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def initialise(self) -> None:
        with closing(self.connection.cursor()) as cursor:
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consents (
                    user_id INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    granted INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, scope),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS chemistry_profiles (
                    user_id INTEGER PRIMARY KEY,
                    question_ratio REAL NOT NULL,
                    turn_balance REAL NOT NULL,
                    sentiment_balance REAL NOT NULL,
                    avg_response_seconds REAL NOT NULL,
                    curiosity_score REAL NOT NULL,
                    word_playfulness REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS match_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    partner_id INTEGER NOT NULL,
                    flow_rating INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                """
            )
            self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    # -- user operations -------------------------------------------------
    def add_user(self, email: str, display_name: Optional[str]) -> User:
        timestamp = datetime.utcnow().strftime(ISO_FORMAT)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO users (email, display_name, created_at) VALUES (?, ?, ?)",
                (email, display_name, timestamp),
            )
            user_id = cursor.lastrowid
        self.connection.commit()
        return User(id=user_id, email=email, display_name=display_name, created_at=datetime.strptime(timestamp, ISO_FORMAT))

    def get_user(self, user_id: int) -> Optional[User]:
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            created_at=datetime.strptime(row["created_at"], ISO_FORMAT),
        )

    # -- consent operations ---------------------------------------------
    def set_consent(self, user_id: int, scope: ConsentScope, granted: bool) -> ConsentDecision:
        timestamp = datetime.utcnow().strftime(ISO_FORMAT)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO consents (user_id, scope, granted, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, scope)
                DO UPDATE SET granted = excluded.granted, updated_at = excluded.updated_at
                """,
                (user_id, scope.value, int(granted), timestamp),
            )
        self.connection.commit()
        return ConsentDecision(
            user_id=user_id,
            scope=scope,
            granted=granted,
            updated_at=datetime.strptime(timestamp, ISO_FORMAT),
        )

    def get_consents(self, user_id: int) -> Dict[ConsentScope, ConsentDecision]:
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM consents WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
        return {
            ConsentScope(row["scope"]): ConsentDecision(
                user_id=user_id,
                scope=ConsentScope(row["scope"]),
                granted=bool(row["granted"]),
                updated_at=datetime.strptime(row["updated_at"], ISO_FORMAT),
            )
            for row in rows
        }

    # -- chemistry profiles ---------------------------------------------
    def upsert_profile(self, profile: ChemistryProfile) -> ChemistryProfile:
        timestamp = profile.updated_at.strftime(ISO_FORMAT)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO chemistry_profiles (
                    user_id, question_ratio, turn_balance, sentiment_balance,
                    avg_response_seconds, curiosity_score, word_playfulness, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    question_ratio = excluded.question_ratio,
                    turn_balance = excluded.turn_balance,
                    sentiment_balance = excluded.sentiment_balance,
                    avg_response_seconds = excluded.avg_response_seconds,
                    curiosity_score = excluded.curiosity_score,
                    word_playfulness = excluded.word_playfulness,
                    updated_at = excluded.updated_at
                """,
                (
                    profile.user_id,
                    profile.question_ratio,
                    profile.turn_balance,
                    profile.sentiment_balance,
                    profile.avg_response_seconds,
                    profile.curiosity_score,
                    profile.word_playfulness,
                    timestamp,
                ),
            )
        self.connection.commit()
        return profile

    def get_profile(self, user_id: int) -> Optional[ChemistryProfile]:
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM chemistry_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return ChemistryProfile(
            user_id=row["user_id"],
            question_ratio=row["question_ratio"],
            turn_balance=row["turn_balance"],
            sentiment_balance=row["sentiment_balance"],
            avg_response_seconds=row["avg_response_seconds"],
            curiosity_score=row["curiosity_score"],
            word_playfulness=row["word_playfulness"],
            updated_at=datetime.strptime(row["updated_at"], ISO_FORMAT),
        )

    def iter_profiles(self, exclude_user: int | None = None) -> Iterator[ChemistryProfile]:
        query = "SELECT * FROM chemistry_profiles"
        params: List[object] = []
        if exclude_user is not None:
            query += " WHERE user_id != ?"
            params.append(exclude_user)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        for row in rows:
            yield ChemistryProfile(
                user_id=row["user_id"],
                question_ratio=row["question_ratio"],
                turn_balance=row["turn_balance"],
                sentiment_balance=row["sentiment_balance"],
                avg_response_seconds=row["avg_response_seconds"],
                curiosity_score=row["curiosity_score"],
                word_playfulness=row["word_playfulness"],
                updated_at=datetime.strptime(row["updated_at"], ISO_FORMAT),
            )

    def reset(self) -> None:
        with closing(self.connection.cursor()) as cursor:
            cursor.executescript(
                """
                DELETE FROM match_feedback;
                DELETE FROM chemistry_profiles;
                DELETE FROM consents;
                DELETE FROM users;
                """
            )
        self.connection.commit()

    # -- feedback -------------------------------------------------------
    def add_feedback(self, user_id: int, partner_id: int, flow_rating: int) -> MatchFeedback:
        timestamp = datetime.utcnow().strftime(ISO_FORMAT)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO match_feedback (user_id, partner_id, flow_rating, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, partner_id, flow_rating, timestamp),
            )
            feedback_id = cursor.lastrowid
        self.connection.commit()
        return MatchFeedback(
            id=feedback_id,
            user_id=user_id,
            partner_id=partner_id,
            flow_rating=flow_rating,
            created_at=datetime.strptime(timestamp, ISO_FORMAT),
        )

    def list_feedback(self, user_id: int) -> List[MatchFeedback]:
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM match_feedback WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cursor.fetchall()
        return [
            MatchFeedback(
                id=row["id"],
                user_id=row["user_id"],
                partner_id=row["partner_id"],
                flow_rating=row["flow_rating"],
                created_at=datetime.strptime(row["created_at"], ISO_FORMAT),
            )
            for row in rows
        ]
