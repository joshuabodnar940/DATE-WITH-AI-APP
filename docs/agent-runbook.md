# Resonance+ Agent-Oriented Build Runbook

This runbook outlines a recommended sequence of prompts and tasks for orchestrating autonomous coding agents (e.g., GPT-5 Agent Mode, Devin, Cursor) to implement the Resonance+ MVP as described in `product-spec.md`.

## 1. Preparation
- Set up a GitHub repository with CI/CD integrations (GitHub Actions).
- Provision Supabase project (Auth, Postgres, Storage) and store service keys securely.
- Ensure agents have access to the specification documents and environment credentials.

## 2. Prompt Sequence Overview
Each prompt should be executed as a separate pull request/task, with human review between steps.

1. **Repo Initialization & Standards**
   - Prompt: _"Create a mono-repo with directories apps/, services/, infra/, ops/, docs/. Configure linting (Black/Ruff for Python, ESLint/Prettier for JS), formatting hooks, MIT license, README, and GitHub Actions for lint/test."_
   - Acceptance: All pipelines green, documentation generated.

2. **Database Schema & Consent Tables**
   - Prompt: _"Using Supabase, define schemas for users, profiles, consents, consent_audit, social_links, messages, conversations, convo_metrics, embeddings, matches, flow_signals, reports, moderation_actions. Add RLS policies and SQL migrations."_
   - Acceptance: Schema matches spec, policies enforce per-user access, migrations executable.

3. **Consent Onboarding UI**
   - Prompt: _"Implement onboarding flow with consent toggles (chat analysis, voice analysis, social scrape), explanations, and audit logging. Include consent management dashboard."_
   - Acceptance: UI matches Figma/wireframes, API endpoints created, audit entries verified in DB.

4. **Feature Extraction Service**
   - Prompt: _"Create FastAPI service with endpoints /extract/text and /extract/social. Implement text metrics (question ratio, sentiment, curiosity), output embeddings via Sentence Transformers, and generate unit tests with synthetic data."_
   - Acceptance: Tests passing, service dockerized, API documented.

5. **Matching Engine**
   - Prompt: _"Build matching microservice that aggregates user embeddings, computes candidate matches with FAISS/pgvector, applies reranker with fairness constraints and diversity penalty. Provide nightly batch job script."_
   - Acceptance: Synthetic evaluation demonstrating mutual score ranking, fairness constraint scaffolding present.

6. **Chat Experience & Flow Meter**
   - Prompt: _"Develop chat UI with E2EE, challenge card insertion, and inline flow meter. Wire backend endpoints for storing encrypted messages and flow signals."_
   - Acceptance: Secure storage verified, flow taps recorded, tests covering encryption pipeline.

7. **Moderation & Safety Tools**
   - Prompt: _"Implement toxicity detection (Perspective/open-source), spam throttling, block/report endpoints, and moderation dashboard with audit logging."_
   - Acceptance: Safety incidents logged, admin dashboard protected by role-based auth.

8. **Explainability & Settings**
   - Prompt: _"Add 'Why this match' explainer with adjustable weights, Fresh Start mode, data export/delete flows, and consent history timeline."_
   - Acceptance: Explanations traceable to metrics, export produces JSON bundle, delete flow wipes embeddings.

9. **Analytics & Bias Monitoring**
   - Prompt: _"Set up analytics job to compute weekly KPIs (flow rate, satisfaction, safety). Implement fairness report comparing match scores across cohorts with DP noise."_
   - Acceptance: Dashboard or reports generated, DP parameters documented.

10. **Deployment Automation**
    - Prompt: _"Configure staging deployment (Supabase + Cloud Run/Render). Add end-to-end tests (Playwright) for onboarding→match→chat→report. Deploy on green builds."_
    - Acceptance: CI/CD pipeline deploys successfully; tests cover happy path and consent revocation.

## 3. Human Oversight Checklist
- Review each PR for adherence to consent & privacy requirements.
- Verify that raw social data is not persisted beyond processing.
- Confirm fairness constraints and bias audits are implemented.
- Conduct manual security assessment before pilot (auth, RLS, key storage).

## 4. Pilot Readiness Criteria
- All critical bugs closed.
- Safety team trained on moderation dashboard and escalation playbook.
- Transparency materials published (privacy policy, model cards, algorithmic explainers).
- Pilot cohort onboarded with clear communication on data use and exit options.

## 5. Future Agent Tasks (Post-MVP)
- Integrate federated learning for on-device feature extraction.
- Expand provider support for social scraping with enhanced consent flows.
- Launch community event tooling (Resonance Salons).
- Build recommendation engine for collaborative prompts/games.

Use this runbook as a living document—update prompts and acceptance criteria as the architecture evolves.
