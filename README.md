# transcript_intelligence
The team is building a product called Transcript Intelligence — a tool that helps different  stakeholders across the company make better decisions using these transcripts. Think support  leaders, sales managers, product managers, engineering leads — each would want something  different from this tool. 

## Implementation Overview

This project was implemented in five phases so the work stays explainable, testable, and easy to present.  
Each phase builds on the previous one, moving from raw transcript data to business-ready insights.

### Phase 1: Clean analysis base

In Phase 1, the goal was to create a reliable one-row-per-meeting foundation that all later phases can reuse.

What was done:
- Read all 100 meeting folders from the dataset.
- Flattened core meeting metadata (title, start/end, duration, participants, domains).
- Added summary fields (topics, overall sentiment, sentiment score).
- Computed utterance-level sentiment distribution (positive, neutral, negative, unknown counts and ratios).
- Added sanity checks for coverage and nulls.

Primary script:
- interview-assignment/scripts/build_phase1_flattened.py

Primary outputs:
- interview-assignment/outputs/phase1/meetings_flattened.csv
- interview-assignment/outputs/phase1/sanity_check.json

Why this matters:
- Every downstream analysis uses the same trusted base table.

### Phase 2: Call-type labeling (support/external/internal)

This phase focused on transparent classification instead of black-box labels.

What was done:
- Built deterministic weighted rules using title patterns, domain composition, and summary/topic language.
- Added confidence scoring and rule traces for auditability.
- Included an explicit ambiguous bucket for low-confidence or low-margin cases.
- Exported a manual-review file for ambiguous meetings.

Primary script:
- interview-assignment/scripts/build_phase2_call_types.py

Primary outputs:
- interview-assignment/outputs/phase2/meetings_call_types.csv
- interview-assignment/outputs/phase2/ambiguous_review.csv
- interview-assignment/outputs/phase2/labeling_report.json

Why this matters:
- Leadership can trust the labels because the reasoning is visible and reviewable.

### Phase 3: Topic/theme categorization pipeline

This phase implemented a hybrid method designed for interview strength: discovery + naming + refinement.

What was done:
- Step A: Unsupervised theme discovery with TF-IDF and KMeans clustering.
- Step B: Assisted naming of clusters using top terms and title context.
- Step C: Deterministic refinement rules for edge cases.
- Produced a final taxonomy within the target range (6 to 12 topics).
- Generated representative transcript snippets for each topic.

Primary script:
- interview-assignment/scripts/build_phase3_topics.py

Primary outputs:
- interview-assignment/outputs/phase3/meetings_with_topics.csv
- interview-assignment/outputs/phase3/topic_taxonomy.json
- interview-assignment/outputs/phase3/topic_counts_by_call_type.csv
- interview-assignment/outputs/phase3/topic_representative_snippets.csv
- interview-assignment/outputs/phase3/cluster_diagnostics.json

Why this matters:
- Converts raw transcript content into a stable business taxonomy that can drive product workflows.

### Phase 4: Sentiment trends with interpretation

This phase moved beyond sentiment charts to business interpretation.

What was done:
- Combined utterance-level sentiment and summary-level sentiment for each meeting.
- Built a consistency check between both sentiment lenses.
- Generated trend cuts by call type, by topic, and over time (weekly).
- Identified most negative outlier meetings and generated root-cause notes.
- Wrote stakeholder-specific interpretation for support, sales/account, and product/engineering.

Primary script:
- interview-assignment/scripts/build_phase4_sentiment.py

Primary outputs:
- interview-assignment/outputs/phase4/meeting_sentiment_consistency.csv
- interview-assignment/outputs/phase4/sentiment_by_call_type.csv
- interview-assignment/outputs/phase4/sentiment_by_topic.csv
- interview-assignment/outputs/phase4/sentiment_over_time_weekly.csv
- interview-assignment/outputs/phase4/most_negative_meetings.csv
- interview-assignment/outputs/phase4/business_interpretation.md

Why this matters:
- Helps teams decide where to intervene first instead of only observing sentiment drift.

### Phase 5: Additional high-value insight modules

This phase implemented three practical insight modules that extend core requirements.

What was done:
- Churn/Risk signal scoring:
	- Combined negative sentiment pressure, renewal language, urgency markers, incident mentions, and concern/churn moments.
- Action-item execution pressure:
	- Parsed action items, inferred function/work type, and scored recurring execution pressure.
- Cross-functional friction map:
	- Detected tension/disagreement markers in transcripts and summaries, then mapped friction by topic and call type.

Primary script:
- interview-assignment/scripts/build_phase5_additional_insights.py

Primary outputs:
- interview-assignment/outputs/phase5/churn_risk_scores.csv
- interview-assignment/outputs/phase5/churn_risk_summary.csv
- interview-assignment/outputs/phase5/action_item_catalog.csv
- interview-assignment/outputs/phase5/action_item_execution_pressure.csv
- interview-assignment/outputs/phase5/cross_functional_friction_meetings.csv
- interview-assignment/outputs/phase5/cross_functional_friction_map.csv
- interview-assignment/outputs/phase5/business_insights_phase5.md

Why this matters:
- Adds prioritization signals leadership can actually operate on week to week.

## Final presentation artifacts

To support the take-home presentation and walkthrough:
- interview-assignment/outputs/final/Executive_Summary.md
- interview-assignment/outputs/final/Slide_Outline_30min.md

These files provide a complete narrative for a 30-minute presentation plus Q&A support.
