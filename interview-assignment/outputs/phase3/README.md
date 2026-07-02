# Phase 3 - Hybrid Topic/Theme Categorization

This phase implements a hybrid approach:

- Step A: Unsupervised theme discovery using custom TF-IDF + NumPy KMeans
- Step B: Assisted naming of clusters from top terms and sample titles
- Step C: Rule refinement for edge cases using deterministic keyword overrides

## Script
- `interview-assignment/scripts/build_phase3_topics.py`

## Inputs
- `interview-assignment/outputs/phase2/meetings_call_types.csv`
- `interview-assignment/dataset/<meeting_id>/summary.json`
- `interview-assignment/dataset/<meeting_id>/transcript.json`

## Outputs
- `interview-assignment/outputs/phase3/meetings_with_topics.csv`
- `interview-assignment/outputs/phase3/topic_taxonomy.json`
- `interview-assignment/outputs/phase3/topic_counts_by_call_type.csv`
- `interview-assignment/outputs/phase3/topic_representative_snippets.csv`
- `interview-assignment/outputs/phase3/cluster_diagnostics.json`

## Final taxonomy (current run)
- Compliance & Audit Readiness
- Identity, Access & Provisioning
- Incident Response & Outage Management
- Platform Reliability & Performance
- Product Roadmap & Engineering Execution
- Renewal, Pricing & Commercial Negotiation
- Security Monitoring & Threat Detection
- Support Troubleshooting & Case Resolution

Total topics: 8

## Notes on transparency
- Every meeting keeps both `cluster_assisted_name` and `final_topic`.
- `cluster_diagnostics.json` captures top cluster terms and naming match scores.
- Refinement rules are deterministic and easy to inspect in code.

## Snippet selection
- Representative snippets are selected from transcript utterances by informativeness score.
- Exactly 3 snippets are emitted per topic for presentation-ready examples.
