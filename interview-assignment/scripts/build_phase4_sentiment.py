#!/usr/bin/env python3
"""Phase 4: Sentiment trends with business interpretation.

Uses both:
- utterance-level sentiment ratios (from phase 2)
- meeting-level summary sentiment (overallSentiment/sentimentScore)

Outputs:
- interview-assignment/outputs/phase4/meeting_sentiment_consistency.csv
- interview-assignment/outputs/phase4/sentiment_by_call_type.csv
- interview-assignment/outputs/phase4/sentiment_by_topic.csv
- interview-assignment/outputs/phase4/sentiment_over_time_weekly.csv
- interview-assignment/outputs/phase4/most_negative_meetings.csv
- interview-assignment/outputs/phase4/business_interpretation.md
- interview-assignment/outputs/phase4/README.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Handles values like 2026-03-16T09:30:00.000Z
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def week_start(dt: datetime) -> datetime:
    # Monday-based week buckets.
    days = dt.weekday()
    return datetime(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo) - timedelta(days=days)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def summary_label_to_score_band(label: str, score: float) -> str:
    label = (label or "").strip().lower()
    if label in {"very-negative", "negative", "mixed-negative"} or score < 3.0:
        return "negative"
    if label in {"very-positive", "positive", "mixed-positive"} or score > 3.6:
        return "positive"
    return "neutral"


def utterance_composite_score(pos_ratio: float, neg_ratio: float) -> float:
    # Maps net utterance sentiment [-1, +1] -> [1, 5].
    net = pos_ratio - neg_ratio
    return clamp(3.0 + 2.0 * net, 1.0, 5.0)


def consistency_bucket(summary_label: str, summary_score: float, utt_score: float) -> str:
    summary_band = summary_label_to_score_band(summary_label, summary_score)
    utt_band = summary_label_to_score_band("", utt_score)
    diff = abs(summary_score - utt_score)

    if summary_band == utt_band and diff <= 0.8:
        return "strong_match"
    if summary_band == utt_band or diff <= 1.2:
        return "partial_match"
    return "mismatch"


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def root_cause_note(summary_topics: str, title: str, summary_text: str) -> str:
    blob = f"{summary_topics} {title} {summary_text}".lower()
    notes: list[str] = []

    if any(k in blob for k in ["outage", "incident", "war room", "failure", "visibility"]):
        notes.append("Outage/incident impact and trust erosion")
    if any(k in blob for k in ["latency", "performance", "degradation", "pipeline"]):
        notes.append("Performance/reliability degradation")
    if any(k in blob for k in ["renewal", "churn", "contract", "pricing", "competitive"]):
        notes.append("Commercial risk in renewal conversation")
    if any(k in blob for k in ["compliance", "audit", "soc 2", "hipaa", "iso"]):
        notes.append("Compliance pressure and delivery risk")
    if any(k in blob for k in ["support case", "ticket", "escalation", "bug", "restore"]):
        notes.append("Open support escalation and unresolved issue burden")

    if not notes:
        return "Mixed friction signals; requires manual readout"
    return "; ".join(notes[:2])


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    var = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return var ** 0.5


def zscore(value: float, values: list[float]) -> float:
    sd = stdev(values)
    if sd == 0:
        return 0.0
    m = sum(values) / len(values)
    return (value - m) / sd


def main() -> None:
    parser = argparse.ArgumentParser(description="Build phase 4 sentiment trend outputs")
    parser.add_argument(
        "--phase2-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase2/meetings_call_types.csv"),
    )
    parser.add_argument(
        "--phase3-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase3/meetings_with_topics.csv"),
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("interview-assignment/dataset"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("interview-assignment/outputs/phase4"),
    )
    args = parser.parse_args()

    phase2_rows = list(csv.DictReader(args.phase2_csv.open("r", encoding="utf-8", newline="")))
    phase3_rows = list(csv.DictReader(args.phase3_csv.open("r", encoding="utf-8", newline="")))

    p3_by_id = {r["meeting_id"]: r for r in phase3_rows}

    combined: list[dict[str, Any]] = []

    # Join phase 2 + phase 3 and compute consistency metrics.
    for r2 in phase2_rows:
        mid = r2["meeting_id"]
        r3 = p3_by_id.get(mid, {})

        pos_ratio = safe_float(r2.get("utt_sent_positive_ratio"))
        neg_ratio = safe_float(r2.get("utt_sent_negative_ratio"))
        neu_ratio = safe_float(r2.get("utt_sent_neutral_ratio"))
        summary_score = safe_float(r2.get("sentiment_score"), 3.0)
        summary_label = r2.get("overall_sentiment", "")

        utt_score = utterance_composite_score(pos_ratio, neg_ratio)
        cons = consistency_bucket(summary_label, summary_score, utt_score)

        summary_json = read_json(args.dataset_dir / mid / "summary.json") or {}
        summary_text = str(summary_json.get("summary", "") or "")

        row = {
            "meeting_id": mid,
            "title": r2.get("title", ""),
            "start_time": r2.get("start_time", ""),
            "call_type": r2.get("call_type", ""),
            "final_topic": r3.get("final_topic", "Unknown"),
            "summary_overall_sentiment": summary_label,
            "summary_sentiment_score": round(summary_score, 4),
            "utt_sent_positive_ratio": round(pos_ratio, 4),
            "utt_sent_neutral_ratio": round(neu_ratio, 4),
            "utt_sent_negative_ratio": round(neg_ratio, 4),
            "utt_composite_score": round(utt_score, 4),
            "summary_utt_score_gap": round(summary_score - utt_score, 4),
            "sentiment_consistency": cons,
            "summary_topics": r2.get("summary_topics", ""),
            "summary_text": summary_text,
        }
        combined.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 1) Meeting consistency table.
    consistency_csv = args.output_dir / "meeting_sentiment_consistency.csv"
    consistency_fields = [
        "meeting_id",
        "title",
        "start_time",
        "call_type",
        "final_topic",
        "summary_overall_sentiment",
        "summary_sentiment_score",
        "utt_sent_positive_ratio",
        "utt_sent_neutral_ratio",
        "utt_sent_negative_ratio",
        "utt_composite_score",
        "summary_utt_score_gap",
        "sentiment_consistency",
    ]
    with consistency_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=consistency_fields)
        w.writeheader()
        for row in combined:
            w.writerow({k: row[k] for k in consistency_fields})

    # 2) Sentiment by call type.
    by_call_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in combined:
        by_call_type[r["call_type"]].append(r)

    call_type_csv = args.output_dir / "sentiment_by_call_type.csv"
    call_type_fields = [
        "call_type",
        "meeting_count",
        "avg_summary_sentiment_score",
        "avg_utt_composite_score",
        "avg_utt_positive_ratio",
        "avg_utt_negative_ratio",
        "negative_dominant_meetings",
        "consistency_strong_match_share",
    ]
    with call_type_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=call_type_fields)
        w.writeheader()
        for ct, rows in sorted(by_call_type.items()):
            w.writerow(
                {
                    "call_type": ct,
                    "meeting_count": len(rows),
                    "avg_summary_sentiment_score": mean([safe_float(r["summary_sentiment_score"]) for r in rows]),
                    "avg_utt_composite_score": mean([safe_float(r["utt_composite_score"]) for r in rows]),
                    "avg_utt_positive_ratio": mean([safe_float(r["utt_sent_positive_ratio"]) for r in rows]),
                    "avg_utt_negative_ratio": mean([safe_float(r["utt_sent_negative_ratio"]) for r in rows]),
                    "negative_dominant_meetings": sum(
                        1 for r in rows if safe_float(r["utt_sent_negative_ratio"]) > safe_float(r["utt_sent_positive_ratio"])
                    ),
                    "consistency_strong_match_share": mean(
                        [1.0 if r["sentiment_consistency"] == "strong_match" else 0.0 for r in rows]
                    ),
                }
            )

    # 3) Sentiment by topic.
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in combined:
        by_topic[r["final_topic"]].append(r)

    topic_csv = args.output_dir / "sentiment_by_topic.csv"
    topic_fields = [
        "topic",
        "meeting_count",
        "avg_summary_sentiment_score",
        "avg_utt_composite_score",
        "avg_utt_positive_ratio",
        "avg_utt_negative_ratio",
        "negative_dominant_meetings",
        "action_item_pressure_hint",
    ]
    with topic_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=topic_fields)
        w.writeheader()
        for topic, rows in sorted(by_topic.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            neg_dom = sum(
                1 for r in rows if safe_float(r["utt_sent_negative_ratio"]) > safe_float(r["utt_sent_positive_ratio"])
            )
            hint = "high" if len(rows) > 0 and (neg_dom / len(rows)) >= 0.35 else "moderate" if neg_dom > 0 else "low"
            w.writerow(
                {
                    "topic": topic,
                    "meeting_count": len(rows),
                    "avg_summary_sentiment_score": mean([safe_float(r["summary_sentiment_score"]) for r in rows]),
                    "avg_utt_composite_score": mean([safe_float(r["utt_composite_score"]) for r in rows]),
                    "avg_utt_positive_ratio": mean([safe_float(r["utt_sent_positive_ratio"]) for r in rows]),
                    "avg_utt_negative_ratio": mean([safe_float(r["utt_sent_negative_ratio"]) for r in rows]),
                    "negative_dominant_meetings": neg_dom,
                    "action_item_pressure_hint": hint,
                }
            )

    # 4) Sentiment over time (weekly).
    weekly: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in combined:
        dt = parse_iso(r["start_time"])
        if not dt:
            continue
        ws = week_start(dt)
        key = ws.date().isoformat()
        weekly[key].append(r)

    weekly_csv = args.output_dir / "sentiment_over_time_weekly.csv"
    weekly_fields = [
        "week_start",
        "meeting_count",
        "avg_summary_sentiment_score",
        "avg_utt_composite_score",
        "avg_utt_positive_ratio",
        "avg_utt_negative_ratio",
        "negative_dominant_share",
    ]
    with weekly_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=weekly_fields)
        w.writeheader()
        for wk in sorted(weekly.keys()):
            rows = weekly[wk]
            neg_dom = sum(
                1 for r in rows if safe_float(r["utt_sent_negative_ratio"]) > safe_float(r["utt_sent_positive_ratio"])
            )
            w.writerow(
                {
                    "week_start": wk,
                    "meeting_count": len(rows),
                    "avg_summary_sentiment_score": mean([safe_float(r["summary_sentiment_score"]) for r in rows]),
                    "avg_utt_composite_score": mean([safe_float(r["utt_composite_score"]) for r in rows]),
                    "avg_utt_positive_ratio": mean([safe_float(r["utt_sent_positive_ratio"]) for r in rows]),
                    "avg_utt_negative_ratio": mean([safe_float(r["utt_sent_negative_ratio"]) for r in rows]),
                    "negative_dominant_share": round(neg_dom / len(rows), 4) if rows else 0.0,
                }
            )

    # 5) Outliers (most negative meetings) + root-cause notes.
    neg_scores = [safe_float(r["utt_sent_negative_ratio"]) for r in combined]
    outliers = []
    for r in combined:
        neg = safe_float(r["utt_sent_negative_ratio"])
        pos = safe_float(r["utt_sent_positive_ratio"])
        summary_score = safe_float(r["summary_sentiment_score"])
        pressure = (neg - pos) + ((3.2 - summary_score) / 3.0)
        outliers.append(
            {
                **r,
                "neg_pressure_score": round(pressure, 4),
                "neg_ratio_zscore": round(zscore(neg, neg_scores), 4),
                "root_cause_note": root_cause_note(r["summary_topics"], r["title"], r["summary_text"]),
            }
        )

    outliers.sort(key=lambda x: x["neg_pressure_score"], reverse=True)
    top_outliers = outliers[:12]

    outlier_csv = args.output_dir / "most_negative_meetings.csv"
    outlier_fields = [
        "meeting_id",
        "title",
        "start_time",
        "call_type",
        "final_topic",
        "summary_overall_sentiment",
        "summary_sentiment_score",
        "utt_sent_positive_ratio",
        "utt_sent_negative_ratio",
        "utt_composite_score",
        "neg_pressure_score",
        "neg_ratio_zscore",
        "root_cause_note",
    ]
    with outlier_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=outlier_fields)
        w.writeheader()
        for r in top_outliers:
            w.writerow({k: r[k] for k in outlier_fields})

    # 6) Business interpretation markdown.
    consistency_counts = Counter(r["sentiment_consistency"] for r in combined)

    support_rows = by_call_type.get("support", [])
    external_rows = by_call_type.get("external", [])
    pe_rows = [r for r in combined if r["call_type"] in {"internal", "ambiguous"}]

    support_neg_share = round(
        sum(1 for r in support_rows if safe_float(r["utt_sent_negative_ratio"]) > safe_float(r["utt_sent_positive_ratio"])) / len(support_rows),
        4,
    ) if support_rows else 0.0
    support_outage_cases = sum(
        1
        for r in support_rows
        if any(k in (r["summary_topics"] or "").lower() for k in ["outage", "latency", "incident", "failure"])
    )

    external_renewal_risk = sum(
        1
        for r in external_rows
        if any(k in (r["summary_topics"] or "").lower() for k in ["renewal", "churn", "pricing", "contract", "competitive"])
        and safe_float(r["summary_sentiment_score"]) <= 3.4
    )

    pe_drop_topics = []
    for topic, rows in by_topic.items():
        filtered = [r for r in rows if r["call_type"] in {"internal", "ambiguous"}]
        if not filtered:
            continue
        avg_score = mean([safe_float(r["summary_sentiment_score"]) for r in filtered])
        neg_share = mean(
            [1.0 if safe_float(r["utt_sent_negative_ratio"]) > safe_float(r["utt_sent_positive_ratio"]) else 0.0 for r in filtered]
        )
        if avg_score <= 3.3 or neg_share >= 0.35:
            pe_drop_topics.append((topic, avg_score, neg_share, len(filtered)))
    pe_drop_topics.sort(key=lambda x: (x[1], -x[2]))

    md_lines = [
        "# Phase 4 - Sentiment Trends and Business Interpretation",
        "",
        "## Consistency check (utterance vs summary sentiment)",
        f"- strong_match: {consistency_counts.get('strong_match', 0)} meetings",
        f"- partial_match: {consistency_counts.get('partial_match', 0)} meetings",
        f"- mismatch: {consistency_counts.get('mismatch', 0)} meetings",
        "",
        "Interpretation:",
        "- The two sentiment lenses are generally aligned where strong/partial matches dominate.",
        "- Mismatch cases should be manually reviewed because they often indicate summary abstraction drift or mixed conversational tone.",
        "",
        "## Trend cuts produced",
        "- Sentiment by call type: sentiment_by_call_type.csv",
        "- Sentiment by topic: sentiment_by_topic.csv",
        "- Sentiment over time (weekly): sentiment_over_time_weekly.csv",
        "- Most negative outliers with root-cause notes: most_negative_meetings.csv",
        "",
        "## Business interpretation",
        "",
        "### Support leaders",
        f"- Negative-dominant share in support calls: {support_neg_share:.2%}.",
        f"- Support meetings with outage/latency/incident signals: {support_outage_cases}.",
        "- Readout: negative spikes are closely tied to reliability incidents and restore/escalation workflows. Prioritize incident communication quality, ETA accuracy, and faster ticket closure for outage-adjacent cases.",
        "",
        "### Sales/account teams",
        f"- External calls with renewal/churn/pricing signals and lower sentiment: {external_renewal_risk}.",
        "- Readout: commercial risk concentrates when competitive pressure and outage memory overlap in renewal conversations. Equip CSM/AM playbooks with reliability proof points and proactive concession strategy.",
        "",
        "### Product/engineering",
        "- Topics where sentiment drops despite action-oriented meetings:",
    ]

    if pe_drop_topics:
        for topic, avg_score, neg_share, n in pe_drop_topics[:6]:
            md_lines.append(
                f"- {topic}: meetings={n}, avg_summary_score={avg_score:.2f}, negative_dominant_share={neg_share:.2%}"
            )
    else:
        md_lines.append("- No major drop topics flagged under current thresholds.")

    md_lines.extend(
        [
            "- Readout: action items alone do not guarantee confidence recovery; reliability and execution transparency need visible follow-through across subsequent meetings.",
            "",
            "## Recommended next actions",
            "1. Create a weekly sentiment-risk review for support + external renewal calls.",
            "2. Add a post-incident customer confidence KPI (sentiment recovery lag by topic).",
            "3. Track action-item completion and correlate with next-meeting sentiment change.",
        ]
    )

    interp_md = args.output_dir / "business_interpretation.md"
    interp_md.write_text("\n".join(md_lines), encoding="utf-8")

    # 7) README
    readme_lines = [
        "# Phase 4 - Sentiment Trend Analysis",
        "",
        "This phase combines utterance-level and summary-level sentiment to generate business-facing trends.",
        "",
        "## Script",
        "- interview-assignment/scripts/build_phase4_sentiment.py",
        "",
        "## Key outputs",
        "- meeting_sentiment_consistency.csv",
        "- sentiment_by_call_type.csv",
        "- sentiment_by_topic.csv",
        "- sentiment_over_time_weekly.csv",
        "- most_negative_meetings.csv",
        "- business_interpretation.md",
        "",
        "## Consistency method",
        "- Utterance composite score is derived from positive vs negative utterance ratios.",
        "- Summary sentiment score/label is compared against utterance composite score.",
        "- Meetings are bucketed into strong_match, partial_match, or mismatch.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    print(f"Wrote: {consistency_csv}")
    print(f"Wrote: {call_type_csv}")
    print(f"Wrote: {topic_csv}")
    print(f"Wrote: {weekly_csv}")
    print(f"Wrote: {outlier_csv}")
    print(f"Wrote: {interp_md}")
    print(f"Wrote: {args.output_dir / 'README.md'}")


if __name__ == "__main__":
    main()
