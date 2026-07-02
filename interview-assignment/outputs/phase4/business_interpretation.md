# Phase 4 - Sentiment Trends and Business Interpretation

## Consistency check (utterance vs summary sentiment)
- strong_match: 67 meetings
- partial_match: 33 meetings
- mismatch: 0 meetings

Interpretation:
- The two sentiment lenses are generally aligned where strong/partial matches dominate.
- Mismatch cases should be manually reviewed because they often indicate summary abstraction drift or mixed conversational tone.

## Trend cuts produced
- Sentiment by call type: sentiment_by_call_type.csv
- Sentiment by topic: sentiment_by_topic.csv
- Sentiment over time (weekly): sentiment_over_time_weekly.csv
- Most negative outliers with root-cause notes: most_negative_meetings.csv

## Business interpretation

### Support leaders
- Negative-dominant share in support calls: 59.26%.
- Support meetings with outage/latency/incident signals: 15.
- Readout: negative spikes are closely tied to reliability incidents and restore/escalation workflows. Prioritize incident communication quality, ETA accuracy, and faster ticket closure for outage-adjacent cases.

### Sales/account teams
- External calls with renewal/churn/pricing signals and lower sentiment: 15.
- Readout: commercial risk concentrates when competitive pressure and outage memory overlap in renewal conversations. Equip CSM/AM playbooks with reliability proof points and proactive concession strategy.

### Product/engineering
- Topics where sentiment drops despite action-oriented meetings:
- Incident Response & Outage Management: meetings=9, avg_summary_score=2.50, negative_dominant_share=88.89%
- Platform Reliability & Performance: meetings=2, avg_summary_score=2.90, negative_dominant_share=50.00%
- Readout: action items alone do not guarantee confidence recovery; reliability and execution transparency need visible follow-through across subsequent meetings.

## Recommended next actions
1. Create a weekly sentiment-risk review for support + external renewal calls.
2. Add a post-incident customer confidence KPI (sentiment recovery lag by topic).
3. Track action-item completion and correlate with next-meeting sentiment change.