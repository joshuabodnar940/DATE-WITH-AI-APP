# Resonance+ MVP Product Specification

_Last updated: 2025-02-16_

## 1. Vision & Value Proposition

Resonance+ is a consent-first dating platform that optimizes for conversational chemistry instead of swipe velocity. By combining in-app conversational signals with optional, user-authorized social media summaries, the system creates adaptive "chemistry vectors" that drive slow, high-quality match curation. The goal is to help rare, systems-oriented thinkers find depth, resonance, and safety in dating.

### Primary Value Pillars
- **Chemistry over looks**: Face-last experience emphasizing prompts, voice notes, and conversation depth before photos.
- **Consent & transparency**: Explicit, revocable data scopes at onboarding and throughout the product. Users always understand how signals are used.
- **Adaptive matching**: Multi-objective AI that optimizes for mutual flow, diversity, and fairness across cohorts.
- **Safety-first operations**: Embedded moderation tooling, toxicity detection, and human review queues.

## 2. Target Users & Use Cases

### Personas
1. **Systems Thinker** – enjoys philosophy, future scenarios, and long-form discussions; frustrated by superficial apps.
2. **Slow Connector** – prefers deeper, fewer conversations; values safety and intentionality.
3. **Curious Builder** – open to co-creating micro-utopias or speculative scenarios; seeks playful intellect.

### Core Jobs-to-Be-Done
- Discover people who match your conversational energy and curiosity.
- Maintain control over how your data is used and revoke access at any time.
- Receive a manageable cadence (3–5 per week) of high-quality introductions.
- Understand why a match was suggested and adjust preferences without starting over.
- Feel safe reporting, blocking, or pausing interactions when necessary.

## 3. Success Metrics (MVP Focus)
- **Conversation Flow Rate**: ≥ 10 back-and-forth messages in at least 60% of active matches.
- **Flow Sentiment**: ≥ 40% of weekly users tap "Great flow" at least once.
- **Conversion to Date**: ≥ 25% of active matches lead to an offline/virtual date with ≥ 4/5 satisfaction.
- **Safety Health**: < 2 confirmed safety incidents per 1k conversations; 100% of reports triaged within 24h.
- **Fairness Parity**: Chemistry score distribution variance ≤ 10% across gender and ethnicity cohorts.

## 4. Product Scope (MVP)

### 4.1 Platforms
- Mobile-responsive web app (React/Next.js or FlutterFlow export) for MVP.
- Native mobile wrappers optional post-MVP.

### 4.2 Key Features
1. **Account Creation & Consent Onboarding**
   - Email/phone-based signup with age verification (18+).
   - Consent toggles for data scopes:
     - In-app message analysis (required for matching).
     - Voice note analysis (optional).
     - Social media summarization (optional per linked account).
   - Audit trail and granular revoke controls accessible from settings.

2. **Profile Setup**
   - Long-form prompts (e.g., "Design a law for a kinder internet").
   - Optional 2-minute voice note introduction.
   - Preferences: genders, distance radius, desired pace (number of matches/week).
   - Face-last photo handling: option to blur or delay photo reveal.

3. **Match Delivery**
   - Weekly batch of 3–5 matches curated by matching service.
   - "Why we matched you" explainer with editable weighting sliders (e.g., Humor, Depth, Tempo).
   - Optional challenge cards to initiate conversation.

4. **Conversation Experience**
   - Secure chat with E2EE; optional voice notes.
   - Inline "flow meter" (Great / Okay / Flat) accessible every 5 messages.
   - Ability to pause, hide, or delete a conversation; honoring consent preferences.

5. **Social Media Integration (Optional)**
   - OAuth or token-based link for Twitter/X, Instagram, or Reddit.
   - Agent fetches recent posts/comments (last 90 days, capped volume), summarizes tone/values.
   - Display summary to user with option to edit or delete before use.

6. **Safety & Moderation**
   - Block/report controls in every conversation.
   - Automated toxicity classifier (text + voice) with throttling.
   - Human moderation dashboard (internal only) with break-glass access logging.

7. **Settings & Data Control**
   - Consent dashboard with history and toggles.
   - Data export (JSON summaries) and delete account (with verified wipe) flows.
   - Fresh Start mode: reset embeddings while retaining account.

### 4.3 Out of Scope (MVP)
- Video chat, live events, algorithmic photo ranking, ad placements, third-party data resale.

## 5. System Architecture Overview

```
apps/
  web/ (Next.js or Flutter app)
services/
  api-gateway/ (FastAPI/Node) – auth, routing, rate limits
  features/ (Python) – text & social feature extraction
  matching/ (Python) – embeddings, reranker, fairness constraints
  moderation/ (Python/Node) – toxicity, abuse handling
infra/
  db/ (Supabase Postgres schema + policies)
  storage/ (User uploads, encrypted)
  queue/ (Task queue for async jobs)
ops/
  ci/ (GitHub Actions)
  monitoring/ (Logging, alerts)
```

- **Client** communicates with `api-gateway` via HTTPS.
- `api-gateway` enforces auth (Supabase auth tokens) and forwards to internal services.
- Feature extraction runs synchronously for chat (low-latency) and asynchronously for social media ingestion.
- Matching service operates nightly to recompute candidate sets and on-demand for refresh requests.
- Moderation service listens to event bus for new messages and flags.
- Data warehouse (optional) receives anonymized aggregates for analytics.

## 6. Data Model (Supabase / Postgres)

### 6.1 Core Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| `users` | Auth-linked accounts | `id`, `email`, `phone`, `dob`, `created_at` |
| `profiles` | Public profile data | `user_id`, `display_name`, `bio`, `voice_note_url`, `photo_url`, `preferences` (JSONB) |
| `consents` | Per-scope consent flags | `user_id`, `scope` (`chat_analysis`, `voice_analysis`, `social_scrape`), `status`, `granted_at`, `revoked_at` |
| `consent_audit` | History of changes | `id`, `user_id`, `scope`, `action`, `timestamp`, `actor` |
| `social_links` | OAuth tokens/meta | `user_id`, `provider`, `account_handle`, `status`, `last_synced_at` |
| `messages` | Encrypted conversation payloads | `id`, `conversation_id`, `sender_id`, `ciphertext`, `sent_at`, `flow_feedback` |
| `conversations` | Match-level threads | `id`, `user_a`, `user_b`, `match_id`, `status`, `created_at`, `closed_at` |
| `convo_metrics` | Derived summaries | `conversation_id`, `metric_type`, `value`, `window_start`, `window_end` |
| `embeddings` | User-level vectors | `user_id`, `vector_type` (`chemistry`, `social_values`), `vector`, `updated_at` |
| `matches` | Match records | `id`, `user_a`, `user_b`, `status`, `score`, `created_at`, `expires_at` |
| `flow_signals` | Explicit feedback | `id`, `conversation_id`, `user_id`, `signal` (`great`, `ok`, `flat`), `message_index`, `timestamp` |
| `reports` | Safety reports | `id`, `reporter_id`, `reported_id`, `conversation_id`, `reason`, `status`, `triaged_at` |
| `moderation_actions` | Enforcement log | `id`, `user_id`, `action`, `reason`, `performed_by`, `timestamp` |

### 6.2 Access Policies
- Row-Level Security: Users can access only their own profiles, consents, social links, and conversations.
- Service-role keys for internal services (matching, moderation) with narrow scopes.
- All consent toggles must be stored transactionally with audit entries.

## 7. Consent & Privacy Requirements (Summary)
- **Explicit consent** for each data scope during onboarding; default is opt-out for non-essential scopes.
- **Revoke anytime**: toggles immediately stop future collection and trigger deletion workflows for derived data (except safety logs).
- **Data minimization**: store only embeddings and short summaries; raw social posts/messages remain client-side unless report triggers safety review.
- **Transparency**: Provide human-readable explanations of features extracted and how they influence matches.
- **Differential Privacy**: Apply DP noise when aggregating metrics for analytics or model updates.

(Full policy in `docs/privacy-consent.md`.)

## 8. AI & Matching Pipeline

### 8.1 Inputs
- **In-app chat**: sequences of messages (text, emojis, optional voice transcripts) with metadata.
- **Flow feedback**: user taps, conversation continuation length.
- **Profile prompts/voice**: onboarding responses.
- **Social summaries** (optional): hashed embeddings of linked accounts.

### 8.2 Feature Extraction
1. **Text Metrics**
   - Question ratio, turn-taking balance, latency distribution.
   - Semantic depth (embedding variance, abstraction level).
   - Sentiment arcs, empathy markers, conflict resolution phrases.
   - Humor/play signals (callbacks, irony, playful negation).
2. **Voice (optional)**
   - Prosody: tempo, energy, warmth, variability.
   - Confidence vs hesitancy (spectral features).
3. **Social Summaries (optional)**
   - Dominant topics (LDA or transformer-based topic modeling).
   - Value orientation (community-driven vs individualistic, future vs present).
   - Interaction style (supportive, debate-heavy, observational).

All features are normalized and concatenated into a **Chemistry Vector** (dimension 64–128). Sensitive attributes are excluded.

### 8.3 Matching Engine
- **Embedding Model**: Bi-encoder (e.g., Sentence Transformers) fine-tuned with contrastive loss on high-flow conversation pairs.
- **Candidate Generation**: FAISS or pgvector for nearest-neighbor retrieval.
- **Reranker**: Multi-objective optimization combining predicted mutual chemistry, diversity penalty, fairness constraints, safety risk score, and freshness (avoid repeat matches).
- **Exploration vs Exploitation**: Contextual bandit to inject serendipitous matches while respecting constraints.
- **Scheduling**: Nightly batch job computes weekly match sets; on-demand recomputation when a user requests refresh (limited frequency).

### 8.4 Feedback Loop
- Flow meter taps, conversation length, and post-date surveys feed supervised labels.
- Federated learning roadmap: plan to move feature extraction to device where feasible; aggregate gradients with DP noise.
- Bias audits run weekly, comparing match quality metrics across demographics.

## 9. Safety & Moderation
- **Automated Filters**: Toxicity detection on outgoing messages (Perspective API or open-source equivalent) with soft block + warning.
- **Rate Limiting**: Prevent rapid-fire copy-paste spam; throttle for suspicious behavior.
- **Human Review**: Internal dashboard surfaces high-severity reports; all access logged.
- **Shadow Bans**: Repeat offenders placed into isolation pending review.
- **Crisis Protocols**: Escalation pathway for self-harm or threat content (trained responders, external resources).

## 10. UX Flow Summary

1. **Welcome & Eligibility**
   - Age check, community pledge.
2. **Create Account**
   - Email/phone verification.
3. **Consent Module**
   - Multi-step wizard explaining scopes with toggles and preview of benefits.
4. **Profile Crafting**
   - Long-form prompts, voice note, optional photo upload (blurred by default).
5. **Preference Setup**
   - Genders, distance, match frequency, conversation styles you enjoy.
6. **Optional Social Link**
   - Connect Twitter/X, Reddit, or Instagram; review generated summary.
7. **Home Dashboard**
   - Weekly matches, status indicators, upcoming refresh timer.
8. **Match Detail**
   - Profile preview, chemistry insights, challenge cards.
9. **Conversation**
   - Secure chat, flow meter, ability to bookmark key moments.
10. **Reflection**
   - After conversation ends or match expires, optional survey + request adjustments.

## 11. Implementation Plan (Agent-Friendly)

### Sprint 0: Repo & Standards
- Initialize mono-repo with linting, formatting, tests, CI pipelines.
- Document contribution guidelines and code of conduct.

### Sprint 1: Auth, Consent, Database
- Implement Supabase schema & RLS policies.
- Build onboarding wizard with consent toggles and audit logging.

### Sprint 2: Profile & Social Link UX
- Long-form prompts, voice upload, optional social OAuth skeleton.
- Consent-based scraping jobs (mock data for now).

### Sprint 3: Feature Extraction Service
- FastAPI microservice with `/extract/text` and `/extract/social` endpoints.
- Unit tests using synthetic conversations and posts.

### Sprint 4: Matching Service v1
- Chemistry vector assembly, nearest-neighbor retrieval, reranker skeleton with fairness placeholders.
- Nightly batch job scaffold (Celery/Temporal/Cloud scheduler).

### Sprint 5: Chat & Flow Meter
- Secure chat UI, flow meter feedback loop, challenge card library.
- API endpoints for storing messages (encrypted) and flow signals.

### Sprint 6: Safety & Moderation
- Toxicity detection integration, block/report flows, moderation dashboard MVP.

### Sprint 7: Analytics & Explainability
- "Why this match" module with adjustable weights.
- Bias dashboard (simple cohort comparison).

### Sprint 8: Pilot Prep
- Seed data, staging deployment, QA checklist, pilot feedback instrumentation.

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Perceived surveillance (social scraping) | Strict consent UX, editable summaries, revoke + delete pipeline. |
| Bias in embeddings | Diverse training dataset, fairness constraints, weekly audits, human oversight. |
| Safety incidents | Proactive toxicity detection, fast human review, shadow bans, crisis protocols. |
| Cold start (no data) | High-signal onboarding prompts, starter challenge cards, initial heuristic matching. |
| Overfitting to high-verbosity users | Normalize metrics by user baseline, apply tempo-aware matching. |

## 13. Open Questions & Future Work
- Expand provider list for social summaries (LinkedIn, TikTok) with ethical guidance.
- Introduce collaborative mini-games to surface chemistry.
- Implement full federated learning for on-device privacy.
- Support polyamorous or non-traditional relationship structures (requires matching redesign).
- Launch community-led Resonance Salons for acquisition and engagement.

---

This spec is designed to be copied into an auto-coder agent as a guiding document. Pair it with the `docs/agent-runbook.md` prompts to orchestrate implementation while maintaining the consent-first ethos central to Resonance+.
