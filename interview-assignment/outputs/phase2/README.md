# Phase 2 - Call Type Labeling (Deterministic + Ambiguity Aware)

This phase assigns each meeting a call type from:
- `support`
- `external`
- `internal`
- `ambiguous`

## Objective
Create a transparent, reproducible labeling system with confidence and explicit uncertainty handling.

## Inputs
- `interview-assignment/outputs/phase1/meetings_flattened.csv`
- `interview-assignment/dataset/<meeting_id>/meeting-info.json`
- `interview-assignment/dataset/<meeting_id>/summary.json`

## Script
- `interview-assignment/scripts/build_phase2_call_types.py`

## Rule design
Weighted deterministic rules are applied to title, email-domain pattern, and summary topics.

### Support signals
- Strong title anchor: `^Support Case #...`
- Incident/troubleshooting keywords in title/topics:
  - urgent, outage, incident, ticket, escalation, troubleshooting, latency, error, bug, restore, failure, SLA breach

### External signals
- Multi-domain meeting (`>=2` email domains)
- Strong title anchor: `^Aegis / ...`
- Customer/account terms in title/topics:
  - customer, renewal, contract, account, pricing, upsell, churn, competitive, service credits

### Internal signals
- Single-domain meeting (`==1` email domain)
- Internal title anchor: includes `internal`
- Team process terms in title/topics:
  - standup, roadmap, sync, retro, sprint, planning, launch readiness, war room, engineering

## Ambiguity policy
A meeting is labeled `ambiguous` if either condition is true:
- top score < `3.0`
- score margin (top - second) < `1.0`

This avoids forced labels when evidence is mixed.

## Outputs
- `interview-assignment/outputs/phase2/meetings_call_types.csv`
- `interview-assignment/outputs/phase2/ambiguous_review.csv`
- `interview-assignment/outputs/phase2/labeling_report.json`

## Current run summary
- Total meetings: 100
- Labels:
  - external: 43
  - support: 27
  - internal: 20
  - ambiguous: 10

## Quick validation checks
- Support title anchor consistency: 27/27 `Support Case` meetings labeled `support`
- External title anchor consistency: 40/40 `Aegis / ...` meetings labeled `external`

## Manual review workflow
Use `ambiguous_review.csv` to manually assign final labels for uncertain meetings.
Recommended review columns:
- `title`
- `email_domains`
- `raw_top_label`
- `score_*`
- `rules_fired`

Keep both values for auditability:
- `call_type` (model/system label)
- `call_type_manual` (human override)
