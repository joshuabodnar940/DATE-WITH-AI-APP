from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, Iterable, Optional
from urllib.parse import parse_qs, urlparse

from .models import ChemistryProfile, ConsentDecision, ConsentScope, MatchCandidate, MatchFeedback, User
from .service import ConversationMessage, ResonanceService
from .storage import Storage


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass(slots=True)
class Response:
    status: int
    body: Any
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})


class ResonanceAPI:
    """Minimal HTTP-style interface for the Resonance+ domain service."""

    def __init__(self, service: ResonanceService | None = None) -> None:
        self.service = service or ResonanceService()

    # -- public dispatch -------------------------------------------------
    def handle(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        query: Optional[dict[str, str]] = None,
    ) -> Response:
        body = body or {}
        query = query or {}
        parts = [segment for segment in path.strip("/").split("/") if segment]

        try:
            if method == "POST" and parts == ["users"]:
                return self._register_user(body)
            if method == "GET" and len(parts) == 2 and parts[0] == "users":
                return self._get_user(int(parts[1]))
            if len(parts) == 3 and parts[0] == "users" and parts[2] == "consents":
                user_id = int(parts[1])
                if method == "GET":
                    return self._get_consents(user_id)
                if method == "PATCH":
                    return self._update_consents(user_id, body)
            if len(parts) == 3 and parts[0] == "users" and parts[2] == "conversations" and method == "POST":
                return self._ingest_conversation(int(parts[1]), body)
            if len(parts) == 3 and parts[0] == "users" and parts[2] == "matches" and method == "GET":
                limit = int(query.get("limit", "3"))
                return self._suggest_matches(int(parts[1]), limit)
            if parts == ["feedback"] and method == "POST":
                return self._submit_feedback(body)
            if len(parts) == 3 and parts[0] == "users" and parts[2] == "feedback" and method == "GET":
                return self._list_feedback(int(parts[1]))
        except PermissionError as exc:
            return Response(status=HTTPStatus.FORBIDDEN, body={"detail": str(exc)})
        except ValueError as exc:
            return Response(status=HTTPStatus.BAD_REQUEST, body={"detail": str(exc)})

        return Response(status=HTTPStatus.NOT_FOUND, body={"detail": "endpoint not found"})

    # -- endpoint implementations ---------------------------------------
    def _register_user(self, data: dict[str, Any]) -> Response:
        email = data.get("email")
        display_name = data.get("display_name")
        if not isinstance(email, str) or not email:
            raise ValueError("email is required")
        consent_flags: dict[ConsentScope, bool] = {}
        for item in data.get("consents", []):
            if not isinstance(item, dict):
                raise ValueError("invalid consent payload")
            try:
                scope = ConsentScope(item["scope"])
            except (KeyError, ValueError) as exc:
                raise ValueError("invalid consent scope") from exc
            consent_flags[scope] = bool(item.get("granted"))
        user = self.service.register_user(email, display_name, consent_flags=consent_flags)
        return Response(status=HTTPStatus.CREATED, body=_serialise_user(user))

    def _get_user(self, user_id: int) -> Response:
        user = self.service.get_user(user_id)
        return Response(status=HTTPStatus.OK, body=_serialise_user(user))

    def _get_consents(self, user_id: int) -> Response:
        consents = self.service.get_consents(user_id)
        payload = [_serialise_consent(consent) for consent in _order_consents(consents.values())]
        return Response(status=HTTPStatus.OK, body=payload)

    def _update_consents(self, user_id: int, data: dict[str, Any]) -> Response:
        if not isinstance(data, list):
            raise ValueError("expected list of consent updates")
        updates = {}
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("invalid consent payload")
            try:
                scope = ConsentScope(item["scope"])
            except (KeyError, ValueError) as exc:
                raise ValueError("invalid consent scope") from exc
            updates[scope] = bool(item.get("granted"))
        consents = self.service.update_consents(user_id, updates)
        payload = [_serialise_consent(consent) for consent in _order_consents(consents.values())]
        return Response(status=HTTPStatus.OK, body=payload)

    def _ingest_conversation(self, user_id: int, data: dict[str, Any]) -> Response:
        messages_payload = data.get("messages")
        if not isinstance(messages_payload, list):
            raise ValueError("messages must be a list")
        parsed_messages = []
        for item in messages_payload:
            if not isinstance(item, dict):
                raise ValueError("invalid message payload")
            parsed_messages.append(
                ConversationMessage(
                    author=item.get("author"),
                    text=item.get("text", ""),
                    timestamp=_parse_timestamp(item.get("timestamp")),
                )
            )
        profile = self.service.ingest_conversation(user_id, parsed_messages)
        return Response(status=HTTPStatus.OK, body=_serialise_profile(profile))

    def _suggest_matches(self, user_id: int, limit: int) -> Response:
        matches = self.service.suggest_matches(user_id, limit=limit)
        return Response(status=HTTPStatus.OK, body=[_serialise_match(candidate) for candidate in matches])

    def _submit_feedback(self, data: dict[str, Any]) -> Response:
        try:
            user_id = int(data.get("user_id"))
            partner_id = int(data.get("partner_id"))
            flow_rating = int(data.get("flow_rating"))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid feedback payload") from exc
        feedback = self.service.submit_feedback(user_id, partner_id, flow_rating)
        return Response(status=HTTPStatus.CREATED, body=_serialise_feedback(feedback))

    def _list_feedback(self, user_id: int) -> Response:
        feedback = self.service.list_feedback(user_id)
        return Response(status=HTTPStatus.OK, body=[_serialise_feedback(item) for item in feedback])


# -- serialisation helpers -----------------------------------------------


def _serialise_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": _iso(user.created_at),
    }


def _serialise_consent(consent: ConsentDecision) -> dict[str, Any]:
    return {
        "scope": consent.scope.value,
        "granted": consent.granted,
        "updated_at": _iso(consent.updated_at),
    }


def _serialise_profile(profile: ChemistryProfile) -> dict[str, Any]:
    payload = asdict(profile)
    payload["updated_at"] = _iso(profile.updated_at)
    return payload


def _serialise_match(candidate: MatchCandidate) -> dict[str, Any]:
    return {
        "user_id": candidate.user_id,
        "score": candidate.score,
        "alignment": candidate.alignment,
    }


def _serialise_feedback(feedback: MatchFeedback) -> dict[str, Any]:
    return {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "partner_id": feedback.partner_id,
        "flow_rating": feedback.flow_rating,
        "created_at": _iso(feedback.created_at),
    }


def _order_consents(consents: Iterable[ConsentDecision]) -> list[ConsentDecision]:
    return sorted(consents, key=lambda decision: decision.scope.value)


def _iso(value: datetime) -> str:
    return value.strftime(ISO_FORMAT)


def _parse_timestamp(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        try:
            if raw.endswith("Z"):
                return datetime.strptime(raw, ISO_FORMAT)
            return datetime.fromisoformat(raw)
        except ValueError as exc:  # pragma: no cover - protective branch
            raise ValueError("invalid timestamp format") from exc
    raise ValueError("timestamp required")


# -- simple HTTP server ---------------------------------------------------


class _HTTPHandler:
    def __init__(self, api: ResonanceAPI) -> None:
        self.api = api

    def __call__(self, environ, start_response):  # type: ignore[override]
        method = environ["REQUEST_METHOD"].upper()
        parsed = urlparse(environ["PATH_INFO"] + ("?" + environ["QUERY_STRING"] if environ["QUERY_STRING"] else ""))
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body_bytes = environ["wsgi.input"].read(length) if length else b""
        body = json.loads(body_bytes.decode("utf-8") or "null") if body_bytes else None
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}

        response = self.api.handle(method, parsed.path, body=body, query=query)
        start_response(f"{response.status} {HTTPStatus(response.status).phrase}", list(response.headers.items()))
        payload = json.dumps(response.body).encode("utf-8") if response.body is not None else b""
        return [payload]


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    from wsgiref.simple_server import make_server

    api = ResonanceAPI()
    handler = _HTTPHandler(api)
    with make_server(host, port, handler) as httpd:  # pragma: no cover - manual use only
        print(f"Serving Resonance+ API on http://{host}:{port}")
        httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Resonance+ HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", default="resonance.db")
    args = parser.parse_args()

    api = ResonanceAPI(ResonanceService(Storage(args.database)))
    handler = _HTTPHandler(api)

    from wsgiref.simple_server import make_server

    with make_server(args.host, args.port, handler) as httpd:  # pragma: no cover - manual use only
        print(f"Serving Resonance+ API on http://{args.host}:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()

