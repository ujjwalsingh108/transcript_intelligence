# Slide Outline - 30 Minute Presentation

## Timing target
- Presentation: 30 minutes
- Recommended Q&A prep: 15 minutes

## Slide-by-slide plan (30 minutes)

### 1) Title and objective (1 min)
- Problem statement: turn raw transcripts into decisions.
- Scope: 100 meetings across support, external, and internal contexts.

### 2) Business framing and stakeholders (2 min)
- Who needs what:
  - support leaders: resolution quality and escalation risk
  - sales/account teams: renewal/churn risk
  - product/engineering: reliability and execution confidence

### 3) Data and quality coverage (2 min)
- 100 meetings, 4,313 utterances, zero missing/null in flattened core.
- Why this matters: credible insights require trusted base data.

### 4) End-to-end pipeline architecture (2 min)
- Phase 1 to Phase 5 flow.
- Show how each phase builds on previous outputs.

### 5) Phase 2: call-type labeling approach (3 min)
- Deterministic rules + confidence + ambiguity bucket.
- Distribution:
  - external 43, support 27, internal 20, ambiguous 10
- Why this is interview-strong: transparent and auditable reasoning.

### 6) Phase 3: topic taxonomy method (3 min)
- Hybrid method:
  - unsupervised discovery
  - assisted naming
  - edge-case refinement
- Final 8-topic taxonomy with counts.

### 7) Theme examples with snippets (3 min)
- Show 2-3 representative snippets from:
  - Support Troubleshooting
  - Incident Response
  - Compliance/Audit
- Explain why these themes are operationally distinct.

### 8) Phase 4: sentiment methodology (2 min)
- Dual-lens sentiment:
  - utterance ratios
  - summary-level sentiment score
- Consistency result:
  - 67 strong matches, 33 partial, 0 mismatch

### 9) Sentiment trends by call type and topic (3 min)
- Support call type has highest persistent negative pressure.
- Incident Response and Support Troubleshooting are dominant negative themes.

### 10) Sentiment over time and outliers (2 min)
- Mid-March trough aligns with incident-heavy weeks.
- Highlight top negative outliers and root-cause notes.

### 11) Phase 5 Insight #1: Churn/Risk scoring (2 min)
- Explain scoring signals: sentiment + renewal + urgency + incident + concern moments.
- Show top risk concentration in Incident Response theme.

### 12) Phase 5 Insight #2: Action-item execution pressure (2 min)
- Explain extraction and grouping by function/work type.
- Highlight recurring pressure in technical remediation and coordination follow-up.

### 13) Phase 5 Insight #3: Cross-functional friction map (2 min)
- Explain friction detection from transcript and summary markers.
- Show hotspot cells:
  - support troubleshooting x support
  - incident response x ambiguous/external

### 14) Recommendations by leadership function (2 min)
- Support: improve incident communication and escalation turnaround.
- Sales/CS: create renewal-risk intervention playbook for post-incident accounts.
- Product/Eng: track sentiment recovery lag and close communication loops.

### 15) Roadmap and KPI operating cadence (1 min)
- 30/60/90 day plan:
  - 30d: operationalize dashboards + weekly risk review
  - 60d: integrate action completion tracking
  - 90d: deploy sentiment recovery KPI and friction hotspot alerts

## Appendix plan (for 15 min Q&A)
- A1: Call-type labeling rules and confidence thresholds
- A2: Topic-clustering diagnostics and naming logic
- A3: Sentiment consistency calculation details
- A4: Risk score formula and weight rationale
- A5: Friction marker dictionary and examples
- A6: Limitations and future improvements

## Demo flow (if asked to show code)
1. Run phase scripts sequentially from scripts folder
2. Open phase outputs in outputs folders
3. Walk through one meeting from raw transcript to final risk/friction interpretation
