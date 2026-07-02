#!/usr/bin/env python3
"""Build Phase 1 flattened meeting table and sanity checks.

This script reads the dataset folders under interview-assignment/dataset and writes:
1) A flattened CSV with one row per meeting.
2) A sanity check JSON with basic quality/coverage metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def safe_read_json(path: Path) -> Any | None:
    """Read JSON file safely, returning None on failure."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def extract_domains(emails: list[str] | None) -> list[str]:
    """Extract unique lowercase domains from email addresses."""
    if not emails:
        return []
    domains = []
    for email in emails:
        if isinstance(email, str) and "@" in email:
            domains.append(email.rsplit("@", 1)[1].strip().lower())
    return sorted(set(domains))


def sentiment_distribution(transcript_json: Any) -> dict[str, Any]:
    """Compute utterance-level sentiment counts and ratios."""
    items = []
    if isinstance(transcript_json, dict):
        data = transcript_json.get("data")
        if isinstance(data, list):
            items = data

    counts: Counter[str] = Counter()
    for row in items:
        if not isinstance(row, dict):
            continue
        st = row.get("sentimentType")
        if isinstance(st, str) and st.strip():
            counts[st.strip().lower()] += 1
        else:
            counts["unknown"] += 1

    total = sum(counts.values())
    positive = counts.get("positive", 0)
    neutral = counts.get("neutral", 0)
    negative = counts.get("negative", 0)
    unknown = counts.get("unknown", 0)

    def ratio(value: int) -> float:
        return round(value / total, 4) if total else 0.0

    return {
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "unknown": unknown,
        "positive_ratio": ratio(positive),
        "neutral_ratio": ratio(neutral),
        "negative_ratio": ratio(negative),
        "unknown_ratio": ratio(unknown),
    }


def build_rows(dataset_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build flattened rows and collect sanity statistics."""
    rows: list[dict[str, Any]] = []
    missing_files: Counter[str] = Counter()

    meeting_dirs = sorted([p for p in dataset_dir.iterdir() if p.is_dir()])

    for meeting_dir in meeting_dirs:
        meeting_id = meeting_dir.name

        meeting_info = safe_read_json(meeting_dir / "meeting-info.json")
        summary = safe_read_json(meeting_dir / "summary.json")
        transcript = safe_read_json(meeting_dir / "transcript.json")

        if meeting_info is None:
            missing_files["meeting-info.json"] += 1
        if summary is None:
            missing_files["summary.json"] += 1
        if transcript is None:
            missing_files["transcript.json"] += 1

        all_emails = []
        if isinstance(meeting_info, dict):
            maybe_emails = meeting_info.get("allEmails")
            if isinstance(maybe_emails, list):
                all_emails = [e for e in maybe_emails if isinstance(e, str)]

        domains = extract_domains(all_emails)

        topics = []
        overall_sentiment = None
        sentiment_score = None
        if isinstance(summary, dict):
            if isinstance(summary.get("topics"), list):
                topics = [t for t in summary["topics"] if isinstance(t, str)]
            overall_sentiment = summary.get("overallSentiment")
            sentiment_score = summary.get("sentimentScore")

        sent_dist = sentiment_distribution(transcript)

        rows.append(
            {
                "meeting_id": meeting_id,
                "title": (meeting_info or {}).get("title") if isinstance(meeting_info, dict) else None,
                "start_time": (meeting_info or {}).get("startTime") if isinstance(meeting_info, dict) else None,
                "end_time": (meeting_info or {}).get("endTime") if isinstance(meeting_info, dict) else None,
                "duration_minutes": (meeting_info or {}).get("duration") if isinstance(meeting_info, dict) else None,
                "participants_count": len(all_emails),
                "email_domains": ";".join(domains),
                "summary_topics": ";".join(topics),
                "overall_sentiment": overall_sentiment,
                "sentiment_score": sentiment_score,
                "utt_sent_total": sent_dist["total"],
                "utt_sent_positive": sent_dist["positive"],
                "utt_sent_neutral": sent_dist["neutral"],
                "utt_sent_negative": sent_dist["negative"],
                "utt_sent_unknown": sent_dist["unknown"],
                "utt_sent_positive_ratio": sent_dist["positive_ratio"],
                "utt_sent_neutral_ratio": sent_dist["neutral_ratio"],
                "utt_sent_negative_ratio": sent_dist["negative_ratio"],
                "utt_sent_unknown_ratio": sent_dist["unknown_ratio"],
            }
        )

    # Sanity stats
    null_counts: Counter[str] = Counter()
    for row in rows:
        for key, value in row.items():
            if value is None or value == "":
                null_counts[key] += 1

    sanity = {
        "meeting_count": len(rows),
        "missing_file_counts": dict(missing_files),
        "null_field_counts": dict(null_counts),
        "participants_summary": {
            "min": min((r["participants_count"] for r in rows), default=0),
            "max": max((r["participants_count"] for r in rows), default=0),
            "avg": round(
                sum(r["participants_count"] for r in rows) / len(rows), 2
            )
            if rows
            else 0,
        },
        "utterance_summary": {
            "meetings_with_zero_utterances": sum(1 for r in rows if r["utt_sent_total"] == 0),
            "total_utterances": sum(r["utt_sent_total"] for r in rows),
        },
        "overall_sentiment_distribution": dict(
            Counter(r["overall_sentiment"] for r in rows if r["overall_sentiment"])
        ),
    }

    return rows, sanity


def write_csv(rows: list[dict[str, Any]], output_csv: Path) -> None:
    """Write flattened rows to CSV."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "meeting_id",
        "title",
        "start_time",
        "end_time",
        "duration_minutes",
        "participants_count",
        "email_domains",
        "summary_topics",
        "overall_sentiment",
        "sentiment_score",
        "utt_sent_total",
        "utt_sent_positive",
        "utt_sent_neutral",
        "utt_sent_negative",
        "utt_sent_unknown",
        "utt_sent_positive_ratio",
        "utt_sent_neutral_ratio",
        "utt_sent_negative_ratio",
        "utt_sent_unknown_ratio",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build flattened meeting table for phase 1.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("interview-assignment/dataset"),
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase1/meetings_flattened.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--sanity-json",
        type=Path,
        default=Path("interview-assignment/outputs/phase1/sanity_check.json"),
        help="Output sanity JSON path",
    )
    args = parser.parse_args()

    if not args.dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {args.dataset_dir}")

    rows, sanity = build_rows(args.dataset_dir)
    write_csv(rows, args.output_csv)

    args.sanity_json.parent.mkdir(parents=True, exist_ok=True)
    args.sanity_json.write_text(json.dumps(sanity, indent=2), encoding="utf-8")

    print(f"Wrote flattened CSV: {args.output_csv}")
    print(f"Wrote sanity report: {args.sanity_json}")
    print(f"Meetings processed: {len(rows)}")


if __name__ == "__main__":
    main()
