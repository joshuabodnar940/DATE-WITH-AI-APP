# Resonance+ MVP Blueprint

This repository contains design artifacts and an in-progress service implementation for **Resonance+**, a consent-first, chemistry-focused dating platform. The codebase now includes a pure Python domain service that captures consent decisions, ingests conversation signals (with explicit permission), and produces chemistry-aligned match suggestions backed by SQLite persistence.

## Contents

- `docs/product-spec.md` — Founder-grade MVP product specification covering product goals, user journeys, system architecture, data models, AI pipelines, safety, fairness, and KPIs.
- `docs/privacy-consent.md` — Consent, privacy, and data-handling framework.
- `docs/agent-runbook.md` — Suggested prompts and sequencing for orchestrating auto-coder agents to implement the MVP.

## Getting Started

### Running the HTTP API

The repository ships with a lightweight HTTP server built with the Python standard library. Start it via:

```bash
python -m resonance.api --host 127.0.0.1 --port 8000 --database resonance.db
```

Endpoints follow a REST-style pattern for user onboarding, consent management, conversation ingestion, match suggestions, and feedback. See `tests/test_api.py` for representative request payloads and expected responses.

### Using the domain service

The prototype targets Python 3.11+ and has no third-party runtime dependencies. You can explore the core functionality from a Python REPL:

```python
>>> from datetime import datetime
>>> from resonance.service import ResonanceService, ConversationMessage
>>> from resonance.models import ConsentScope
>>> service = ResonanceService()
>>> user = service.register_user("you@example.com", "You", consent_flags={ConsentScope.IN_APP_ANALYSIS: True})
>>> _ = service.ingest_conversation(user.id, [
...     ConversationMessage(author="self", text="What inspires you?", timestamp=datetime.utcnow()),
...     ConversationMessage(author="partner", text="Collaborative futures!", timestamp=datetime.utcnow()),
... ])
>>> service.suggest_matches(user.id)
[]
```

The storage layer defaults to an in-memory SQLite database. Provide a file path to persist data between sessions: `ResonanceService(Storage("resonance.db"))`.

### Tests

Run the automated test suite with:

```bash
pytest
```

### Next steps

Review the product spec first, then follow the agent runbook to extend the implementation using your preferred autonomous coding agent. Ensure all development adheres to the consent and privacy commitments documented in `docs/privacy-consent.md`.
