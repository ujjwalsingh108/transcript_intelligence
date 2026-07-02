# Transcript Intelligence - Executive Summary

## Audience
Product and engineering leadership, with implications for support and customer-facing teams.

## Objective
Analyze 100 transcript meetings and build a practical intelligence layer that:
- categorizes call types and themes,
- tracks sentiment shifts and risk,
- surfaces operational pressure and cross-functional friction,
- and drives decision-ready recommendations.

## Dataset and coverage
- Meetings processed: 100
- Utterances analyzed: 4,313
- Missing core files: 0
- Null field counts in flattened base: 0

## What was built (Phases 1-5)

### 1) Reproducible data foundation
- Built a flattened meeting table with metadata, domains, summary fields, and utterance-level sentiment distributions.
- Output quality checks validate complete coverage and schema consistency.

### 2) Transparent call-type classification
- Deterministic rule system with confidence + explicit ambiguity bucket.
- Final distribution:
  - external: 43
  - support: 27
  - internal: 20
  - ambiguous: 10
- Reasoning-first approach (rules fired + margin/confidence) makes labels auditable.

### 3) Hybrid theme categorization
- Step A: unsupervised clustering (TF-IDF + KMeans)
- Step B: assisted cluster naming
- Step C: rule refinement for edge cases
- Final taxonomy: 8 topics
  - Support Troubleshooting & Case Resolution (33)
  - Compliance & Audit Readiness (27)
  - Incident Response & Outage Management (20)
  - Identity, Access & Provisioning (8)
  - Renewal, Pricing & Commercial Negotiation (6)
  - Product Roadmap & Engineering Execution (3)
  - Platform Reliability & Performance (2)
  - Security Monitoring & Threat Detection (1)

### 4) Sentiment trends + business interpretation
- Combined utterance-level sentiment with summary-level sentiment score/label.
- Consistency check:
  - strong_match: 67
  - partial_match: 33
  - mismatch: 0
- Key trend cuts:
  - by call type:
    - support has lower sentiment and high negative-dominance (16 of 27)
    - ambiguous and incident contexts are most negative
  - by topic:
    - Incident Response & Outage Management has the strongest negative pressure
    - Support Troubleshooting remains a persistent drag theme
  - over time:
    - pronounced mid-March trough (week of 2026-03-09: negative_dominant_share 92.31%)
  - outliers:
    - most negative meetings are outage/incident heavy with trust and visibility concerns

### 5) Additional high-value insight modules

#### A. Churn/Risk signal scoring
- Combined negative sentiment + renewal language + urgency + incident mentions + key-moment concern signals.
- Highest risk concentration:
  - Incident Response & Outage Management (avg risk 68.6; 9 critical)
  - Support call type remains elevated (avg risk 48.23)

#### B. Action-item execution pressure
- Parsed action items, inferred owner/function, and scored recurring execution pressure.
- Highest pressure work types:
  - technical_remediation (52.36)
  - coordination_followup (51.99)
  - analysis_reporting (51.33)
- Insight: coordination and remediation workload recurrence suggests risk of delayed confidence recovery.

#### C. Cross-functional friction map
- Detected tension/disagreement markers in summaries + transcripts and mapped by topic/call type.
- Highest friction pockets:
  - Support Troubleshooting x support (avg friction 50.14; 11 high-friction meetings)
  - Incident Response x ambiguous (avg friction 63.22; 4 high-friction meetings)

## Leadership takeaways

### Support leadership
- Outage-adjacent support cases are the largest source of negative sentiment and friction.
- Focus areas:
  - tighter incident communication SLAs,
  - clearer ETA/risk communication templates,
  - faster escalation-to-resolution loops.

### Sales/account leadership
- Renewal-risk signals are amplified when incident memory remains active in customer conversations.
- Focus areas:
  - pre-emptive recovery narrative in renewal cycles,
  - account-specific reliability proof points,
  - concession guardrails for high-risk renewals.

### Product/engineering leadership
- Action items are abundant, but sentiment only recovers when execution confidence is visible and sustained.
- Focus areas:
  - close the loop on technical remediation + customer communication jointly,
  - track sentiment recovery lag after major incidents,
  - prioritize themes with both high risk and high friction.

## Recommended next-quarter operating metrics
1. Sentiment Recovery Lag: days from incident peak to neutral/positive trend normalization.
2. Risk-Weighted Renewal Exposure: count and ARR share of high-risk renewal meetings.
3. Execution Pressure Index: recurring action-item burden by work type/function.
4. Friction Hotspot Index: topic x call-type cells with persistent high friction.

## Closing
The pipeline demonstrates that transcript intelligence can move beyond summaries to decision intelligence: identifying who is at risk, where execution is bottlenecked, and which cross-functional interactions require intervention first.
