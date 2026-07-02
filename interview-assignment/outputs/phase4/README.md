# Phase 4 - Sentiment Trend Analysis

This phase combines utterance-level and summary-level sentiment to generate business-facing trends.

## Script
- interview-assignment/scripts/build_phase4_sentiment.py

## Key outputs
- meeting_sentiment_consistency.csv
- sentiment_by_call_type.csv
- sentiment_by_topic.csv
- sentiment_over_time_weekly.csv
- most_negative_meetings.csv
- business_interpretation.md

## Consistency method
- Utterance composite score is derived from positive vs negative utterance ratios.
- Summary sentiment score/label is compared against utterance composite score.
- Meetings are bucketed into strong_match, partial_match, or mismatch.