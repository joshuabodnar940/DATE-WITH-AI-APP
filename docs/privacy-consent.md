# Resonance+ Consent, Privacy, and Data Handling Framework

## 1. Principles
- **Explicit consent** for every data scope; nothing is scraped or analyzed without opt-in.
- **Revocability**: Users can pause or revoke consent at any time; revocation triggers deletion workflows for derived data.
- **Minimization**: Store only derived embeddings and summaries whenever possible. Raw message content remains on device or encrypted.
- **Transparency**: Explain how data is used, provide model cards, and expose "Why this match" rationale.
- **Safety-first overrides**: Break-glass access allowed only for active safety investigations with audit logging.

## 2. Consent Scopes

| Scope | Required? | Data Types | Purpose | Storage |
|-------|-----------|-----------|---------|---------|
| `chat_analysis` | Yes | In-app text messages, flow taps | Chemistry modeling, safety monitoring | Encrypted raw messages (short retention), derived metrics + embeddings |
| `voice_analysis` | Optional | Voice notes (in-app) | Prosody features for chemistry vector | Transient processing, derived prosody metrics |
| `social_scrape` | Optional | Posts/comments from linked accounts | Values & style enrichment | Summaries + embeddings only; raw content discarded post-processing |

## 3. User Controls
- Consent toggles in onboarding and Settings → Privacy.
- Each toggle displays benefits, data used, and ability to pause or delete history.
- "Download my data" exports embeddings, summaries, and metadata in JSON.
- "Delete my account" wipes profile, matches, conversations, and vectors (with 30-day safety hold for active investigations).

## 4. Data Flows
1. **In-App Messages**
   - Messages sent → encrypted at rest.
   - Feature extraction service computes conversation metrics in real time.
   - After 90 days, raw messages are pruned unless conversation is reported; metrics retained.
2. **Voice Notes**
   - Uploaded voice stored encrypted.
   - On consent, speech-to-text + prosody metrics computed; raw waveform deleted after 30 days.
3. **Social Media**
   - User authorizes via OAuth/token.
   - Limited fetch (last 90 days, 500 items max) → summarizer extracts tone/values → raw items purged.
   - User reviews summary before it is incorporated into embeddings.
4. **Safety Reports**
   - Copy of relevant conversation retained for investigation; access logged.
   - Upon resolution, data is anonymized or deleted per policy.

## 5. Security Posture
- End-to-end encryption for chats; key escrow only for user-initiated safety reports.
- Row-level security in database ensuring users access only their own records.
- Secrets stored in managed vault (e.g., Supabase secrets, HashiCorp Vault).
- Regular penetration testing and red-team drills focusing on data exfiltration scenarios.

## 6. Differential Privacy & Analytics
- Aggregate analytics apply calibrated DP noise to protect individual contributions.
- No third-party trackers; analytics limited to first-party privacy-preserving tools.
- Model updates use federated learning roadmap; interim approach uses anonymized batches with DP clipping.

## 7. Compliance
- GDPR and CCPA ready: data access, correction, deletion, portability supported.
- Age gating (18+) with KYC/ID verification provider.
- Incident response playbook aligned with SOC 2 and ISO 27001 best practices.

## 8. Audit & Governance
- Quarterly privacy review covering data flows, retention, and consent logs.
- Ethics board reviews algorithmic fairness reports and approves major model changes.
- Public transparency report summarizing safety incidents, data requests, and algorithm updates.

## 9. Open Questions
- Determine regional data residency requirements.
- Evaluate feasibility of on-device encryption keys controlled solely by user.
- Plan for community moderation involvement while preserving privacy guarantees.
