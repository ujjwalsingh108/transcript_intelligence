#!/usr/bin/env python3
"""Phase 5: Additional high-value insights.

Implements:
1) Churn/Risk signal scoring
2) Action-item execution pressure
3) Cross-functional friction map

Outputs:
- interview-assignment/outputs/phase5/churn_risk_scores.csv
- interview-assignment/outputs/phase5/churn_risk_summary.csv
- interview-assignment/outputs/phase5/action_item_catalog.csv
- interview-assignment/outputs/phase5/action_item_execution_pressure.csv
- interview-assignment/outputs/phase5/cross_functional_friction_meetings.csv
- interview-assignment/outputs/phase5/cross_functional_friction_map.csv
- interview-assignment/outputs/phase5/business_insights_phase5.md
- interview-assignment/outputs/phase5/README.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def contains_any(blob: str, patterns: list[str]) -> bool:
    return any(re.search(p, blob, flags=re.IGNORECASE) for p in patterns)


def count_any(blob: str, patterns: list[str]) -> int:
    c = 0
    for p in patterns:
        c += len(re.findall(p, blob, flags=re.IGNORECASE))
    return c


def infer_owner_and_text(action_item: str) -> tuple[str, str]:
    # Common format: "Name: action text"
    if ":" in action_item:
        left, right = action_item.split(":", 1)
        owner = left.strip()
        text = right.strip()
        if owner and text:
            return owner, text
    return "Unspecified", action_item.strip()


def infer_function(text: str) -> str:
    t = text.lower()
    if contains_any(t, [r"customer|renewal|account|contract|pricing|communication|ticket update"]):
        return "customer_success_sales"
    if contains_any(t, [r"deploy|pipeline|node|infrastructure|engineering|fix|rollout|implementation|monitoring"]):
        return "engineering"
    if contains_any(t, [r"support|ticket|case|escalation|triage|incident"]):
        return "support"
    if contains_any(t, [r"audit|compliance|soc\s*2|iso|hipaa|pci|evidence|report"]):
        return "compliance_security"
    if contains_any(t, [r"analysis|summary|postmortem|review|report"]):
        return "program_management"
    return "other"


def infer_work_type(text: str) -> str:
    t = text.lower()
    if contains_any(t, [r"send|share|provide|prepare|draft|update|follow up|schedule|coordinate|confirm"]):
        return "coordination_followup"
    if contains_any(t, [r"customer communication|status update|update customers|communication"]):
        return "customer_communication"
    if contains_any(t, [r"deploy|rollout|implementation|fix|patch|node|pipeline|breaker"]):
        return "technical_remediation"
    if contains_any(t, [r"report|analysis|summary|postmortem|review"]):
        return "analysis_reporting"
    if contains_any(t, [r"audit|compliance|soc\s*2|iso|hipaa|pci"]):
        return "compliance_followthrough"
    if contains_any(t, [r"ticket|case|escalation|triage"]):
        return "support_followup"
    if contains_any(t, [r"contract|renewal|pricing|quote|discount"]):
        return "commercial_followup"
    return "general_followup"


def risk_band(score: float) -> str:
    if score >= 70:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build phase 5 additional insights outputs")
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
        "--phase4-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase4/meeting_sentiment_consistency.csv"),
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("interview-assignment/dataset"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("interview-assignment/outputs/phase5"),
    )
    args = parser.parse_args()

    p2_rows = list(csv.DictReader(args.phase2_csv.open("r", encoding="utf-8", newline="")))
    p3_rows = list(csv.DictReader(args.phase3_csv.open("r", encoding="utf-8", newline="")))
    p4_rows = list(csv.DictReader(args.phase4_csv.open("r", encoding="utf-8", newline="")))

    p3_by_id = {r["meeting_id"]: r for r in p3_rows}
    p4_by_id = {r["meeting_id"]: r for r in p4_rows}

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # 1) Churn/Risk signal scoring
    # ---------------------------------------------------------------------
    risk_rows: list[dict[str, Any]] = []

    for r2 in p2_rows:
        mid = r2["meeting_id"]
        p3 = p3_by_id.get(mid, {})
        p4 = p4_by_id.get(mid, {})

        title = r2.get("title", "")
        summary_topics = r2.get("summary_topics", "")
        summary_text = ""
        summary_json = read_json(args.dataset_dir / mid / "summary.json") or {}
        summary_text = str(summary_json.get("summary", "") or "")
        key_moments = summary_json.get("keyMoments", [])
        if not isinstance(key_moments, list):
            key_moments = []

        blob = f"{title} {summary_topics} {summary_text}".lower()

        neg_ratio = safe_float(r2.get("utt_sent_negative_ratio"))
        pos_ratio = safe_float(r2.get("utt_sent_positive_ratio"))
        summary_score = safe_float(r2.get("sentiment_score"), 3.0)

        # Signal components (0..1)
        sentiment_pressure = clamp((neg_ratio - pos_ratio + 1.0) / 2.0, 0.0, 1.0)
        renewal_signal = 1.0 if contains_any(blob, [r"renewal", r"contract", r"pricing", r"churn", r"competitive"]) else 0.0
        urgency_signal = 1.0 if contains_any(blob, [r"urgent", r"escalation", r"priority", r"p1|p2", r"critical"]) else 0.0
        incident_signal = 1.0 if contains_any(blob, [r"outage", r"incident", r"downtime", r"failure", r"visibility loss"]) else 0.0

        churn_keymoments = sum(
            1
            for km in key_moments
            if isinstance(km, dict) and str(km.get("type", "")).lower() in {"churn_signal", "concern"}
        )
        keymoment_signal = clamp(churn_keymoments / 2.0, 0.0, 1.0)

        summary_penalty = clamp((3.4 - summary_score) / 2.4, 0.0, 1.0)

        # Weighted score in [0,100]
        score = 100.0 * (
            0.30 * sentiment_pressure
            + 0.22 * renewal_signal
            + 0.16 * urgency_signal
            + 0.16 * incident_signal
            + 0.10 * keymoment_signal
            + 0.06 * summary_penalty
        )

        risk_rows.append(
            {
                "meeting_id": mid,
                "title": title,
                "call_type": r2.get("call_type", ""),
                "final_topic": p3.get("final_topic", "Unknown"),
                "sentiment_pressure": round(sentiment_pressure, 4),
                "renewal_signal": round(renewal_signal, 4),
                "urgency_signal": round(urgency_signal, 4),
                "incident_signal": round(incident_signal, 4),
                "keymoment_signal": round(keymoment_signal, 4),
                "summary_penalty": round(summary_penalty, 4),
                "churn_risk_score": round(score, 2),
                "risk_band": risk_band(score),
            }
        )

    risk_rows.sort(key=lambda x: x["churn_risk_score"], reverse=True)

    churn_csv = args.output_dir / "churn_risk_scores.csv"
    churn_fields = [
        "meeting_id",
        "title",
        "call_type",
        "final_topic",
        "sentiment_pressure",
        "renewal_signal",
        "urgency_signal",
        "incident_signal",
        "keymoment_signal",
        "summary_penalty",
        "churn_risk_score",
        "risk_band",
    ]
    with churn_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=churn_fields)
        w.writeheader()
        w.writerows(risk_rows)

    # Aggregated churn/risk summary by call type and topic.
    by_ct = defaultdict(list)
    by_topic = defaultdict(list)
    for r in risk_rows:
        by_ct[r["call_type"]].append(r)
        by_topic[r["final_topic"]].append(r)

    summary_csv = args.output_dir / "churn_risk_summary.csv"
    summary_fields = ["dimension", "value", "meeting_count", "avg_risk_score", "critical_count", "high_count"]
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary_fields)
        w.writeheader()
        for ct, rows in sorted(by_ct.items()):
            w.writerow(
                {
                    "dimension": "call_type",
                    "value": ct,
                    "meeting_count": len(rows),
                    "avg_risk_score": mean([safe_float(r["churn_risk_score"]) for r in rows]),
                    "critical_count": sum(1 for r in rows if r["risk_band"] == "critical"),
                    "high_count": sum(1 for r in rows if r["risk_band"] == "high"),
                }
            )
        for topic, rows in sorted(by_topic.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            w.writerow(
                {
                    "dimension": "topic",
                    "value": topic,
                    "meeting_count": len(rows),
                    "avg_risk_score": mean([safe_float(r["churn_risk_score"]) for r in rows]),
                    "critical_count": sum(1 for r in rows if r["risk_band"] == "critical"),
                    "high_count": sum(1 for r in rows if r["risk_band"] == "high"),
                }
            )

    # ---------------------------------------------------------------------
    # 2) Action-item execution pressure
    # ---------------------------------------------------------------------
    action_catalog: list[dict[str, Any]] = []

    for r2 in p2_rows:
        mid = r2["meeting_id"]
        p3 = p3_by_id.get(mid, {})
        summary_json = read_json(args.dataset_dir / mid / "summary.json") or {}
        action_items = summary_json.get("actionItems", [])
        if not isinstance(action_items, list):
            action_items = []

        neg_ratio = safe_float(r2.get("utt_sent_negative_ratio"))
        summary_score = safe_float(r2.get("sentiment_score"), 3.0)

        for idx, ai in enumerate(action_items, start=1):
            text_raw = str(ai)
            owner, ai_text = infer_owner_and_text(text_raw)
            function = infer_function(ai_text)
            work_type = infer_work_type(ai_text)
            urgency_flag = 1 if contains_any(ai_text, [r"today|asap|urgent|by\s+\w+day|within\s+the\s+hour|immediately"]) else 0

            action_catalog.append(
                {
                    "meeting_id": mid,
                    "action_item_index": idx,
                    "call_type": r2.get("call_type", ""),
                    "final_topic": p3.get("final_topic", "Unknown"),
                    "owner": owner,
                    "owner_function": function,
                    "work_type": work_type,
                    "action_item_text": ai_text,
                    "urgency_flag": urgency_flag,
                    "meeting_negative_ratio": round(neg_ratio, 4),
                    "meeting_sentiment_score": round(summary_score, 4),
                }
            )

    catalog_csv = args.output_dir / "action_item_catalog.csv"
    catalog_fields = [
        "meeting_id",
        "action_item_index",
        "call_type",
        "final_topic",
        "owner",
        "owner_function",
        "work_type",
        "action_item_text",
        "urgency_flag",
        "meeting_negative_ratio",
        "meeting_sentiment_score",
    ]
    with catalog_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=catalog_fields)
        w.writeheader()
        w.writerows(action_catalog)

    # Recurring unresolved pressure by work_type (proxy via recurrence + urgency + negative context).
    by_work = defaultdict(list)
    for a in action_catalog:
        by_work[a["work_type"]].append(a)

    pressure_rows = []
    for wt, rows in sorted(by_work.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        recurrence = len(rows)
        urgency_share = mean([safe_float(r["urgency_flag"]) for r in rows])
        avg_neg = mean([safe_float(r["meeting_negative_ratio"]) for r in rows])
        avg_sent = mean([safe_float(r["meeting_sentiment_score"]) for r in rows])

        # Recurring unresolved proxy score in [0,100].
        recurrence_norm = clamp(recurrence / 25.0, 0.0, 1.0)
        sentiment_penalty = clamp((3.4 - avg_sent) / 2.4, 0.0, 1.0)
        pressure = 100.0 * (0.45 * recurrence_norm + 0.25 * urgency_share + 0.20 * avg_neg + 0.10 * sentiment_penalty)

        top_functions = Counter(r["owner_function"] for r in rows).most_common(3)
        pressure_rows.append(
            {
                "work_type": wt,
                "action_item_count": recurrence,
                "avg_meeting_negative_ratio": round(avg_neg, 4),
                "avg_meeting_sentiment_score": round(avg_sent, 4),
                "urgency_share": round(urgency_share, 4),
                "execution_pressure_score": round(pressure, 2),
                "dominant_functions": ";".join(f"{k}:{v}" for k, v in top_functions),
            }
        )

    pressure_rows.sort(key=lambda x: x["execution_pressure_score"], reverse=True)

    pressure_csv = args.output_dir / "action_item_execution_pressure.csv"
    pressure_fields = [
        "work_type",
        "action_item_count",
        "avg_meeting_negative_ratio",
        "avg_meeting_sentiment_score",
        "urgency_share",
        "execution_pressure_score",
        "dominant_functions",
    ]
    with pressure_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pressure_fields)
        w.writeheader()
        w.writerows(pressure_rows)

    # ---------------------------------------------------------------------
    # 3) Cross-functional friction map
    # ---------------------------------------------------------------------
    friction_meetings = []

    disagreement_markers = [
        r"frustrat", r"pushback", r"concern", r"credibility issue", r"escalat", r"blocked", r"delay",
        r"miss(ed|ing)", r"not acceptable", r"can't", r"cannot", r"risk", r"heated", r"vocal",
        r"disagree", r"tension", r"conflict", r"urgent",
    ]

    for r2 in p2_rows:
        mid = r2["meeting_id"]
        p3 = p3_by_id.get(mid, {})
        summary_json = read_json(args.dataset_dir / mid / "summary.json") or {}
        transcript_json = read_json(args.dataset_dir / mid / "transcript.json") or {}

        summary_blob = f"{r2.get('title','')} {summary_json.get('summary','')} {r2.get('summary_topics','')}".lower()
        summary_hits = count_any(summary_blob, disagreement_markers)

        key_moments = summary_json.get("keyMoments", [])
        if not isinstance(key_moments, list):
            key_moments = []
        keymoment_hits = sum(
            1
            for km in key_moments
            if isinstance(km, dict) and str(km.get("type", "")).lower() in {"concern", "churn_signal", "technical_issue"}
        )

        transcript_rows = transcript_json.get("data", []) if isinstance(transcript_json, dict) else []
        if not isinstance(transcript_rows, list):
            transcript_rows = []

        transcript_hits = 0
        speaker_counter = Counter()
        for tr in transcript_rows:
            if not isinstance(tr, dict):
                continue
            sent = str(tr.get("sentence", ""))
            hits = count_any(sent.lower(), disagreement_markers)
            if hits > 0:
                transcript_hits += hits
                speaker = str(tr.get("speaker_name", "Unknown"))
                speaker_counter[speaker] += hits

        neg_ratio = safe_float(r2.get("utt_sent_negative_ratio"))
        pos_ratio = safe_float(r2.get("utt_sent_positive_ratio"))
        summary_score = safe_float(r2.get("sentiment_score"), 3.0)

        # Friction score in [0,100].
        discourse_tension = clamp((summary_hits + transcript_hits + keymoment_hits) / 18.0, 0.0, 1.0)
        sentiment_tension = clamp((neg_ratio - pos_ratio + 1.0) / 2.0, 0.0, 1.0)
        confidence_penalty = clamp((3.4 - summary_score) / 2.4, 0.0, 1.0)

        friction_score = 100.0 * (0.5 * discourse_tension + 0.35 * sentiment_tension + 0.15 * confidence_penalty)

        friction_meetings.append(
            {
                "meeting_id": mid,
                "title": r2.get("title", ""),
                "call_type": r2.get("call_type", ""),
                "final_topic": p3.get("final_topic", "Unknown"),
                "summary_marker_hits": summary_hits,
                "keymoment_hits": keymoment_hits,
                "transcript_marker_hits": transcript_hits,
                "top_friction_speakers": ";".join(f"{k}:{v}" for k, v in speaker_counter.most_common(3)),
                "utt_negative_ratio": round(neg_ratio, 4),
                "summary_sentiment_score": round(summary_score, 4),
                "friction_score": round(friction_score, 2),
            }
        )

    friction_meetings.sort(key=lambda x: x["friction_score"], reverse=True)

    friction_meeting_csv = args.output_dir / "cross_functional_friction_meetings.csv"
    friction_meeting_fields = [
        "meeting_id",
        "title",
        "call_type",
        "final_topic",
        "summary_marker_hits",
        "keymoment_hits",
        "transcript_marker_hits",
        "top_friction_speakers",
        "utt_negative_ratio",
        "summary_sentiment_score",
        "friction_score",
    ]
    with friction_meeting_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=friction_meeting_fields)
        w.writeheader()
        w.writerows(friction_meetings)

    # Map by topic x call type.
    matrix = defaultdict(list)
    for fm in friction_meetings:
        key = (fm["final_topic"], fm["call_type"])
        matrix[key].append(fm)

    friction_map_rows = []
    for (topic, call_type), rows in sorted(matrix.items(), key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1])):
        friction_map_rows.append(
            {
                "topic": topic,
                "call_type": call_type,
                "meeting_count": len(rows),
                "avg_friction_score": mean([safe_float(r["friction_score"]) for r in rows]),
                "high_friction_meetings": sum(1 for r in rows if safe_float(r["friction_score"]) >= 65),
            }
        )

    friction_map_csv = args.output_dir / "cross_functional_friction_map.csv"
    friction_map_fields = [
        "topic",
        "call_type",
        "meeting_count",
        "avg_friction_score",
        "high_friction_meetings",
    ]
    with friction_map_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=friction_map_fields)
        w.writeheader()
        w.writerows(friction_map_rows)

    # ---------------------------------------------------------------------
    # Business narrative markdown
    # ---------------------------------------------------------------------
    top_risk = risk_rows[:10]
    top_pressure = pressure_rows[:6]
    top_friction = friction_meetings[:10]

    md_lines = [
        "# Phase 5 - Additional Insights",
        "",
        "## 1) Churn/Risk signal scoring",
        "Signals combined:",
        "- Negative sentiment pressure (utterance-level)",
        "- Renewal/commercial language",
        "- Urgency markers",
        "- Incident/outage mentions",
        "- Churn/concern key moments",
        "",
        "Top risk meetings:",
    ]
    for r in top_risk[:8]:
        md_lines.append(
            f"- {r['meeting_id']} | {r['call_type']} | {r['final_topic']} | score={r['churn_risk_score']} ({r['risk_band']}) | {r['title']}"
        )

    md_lines.extend(
        [
            "",
            "## 2) Action-item execution pressure",
            "Method:",
            "- Parse action items from summaries",
            "- Infer owner/function and work type",
            "- Score pressure by recurrence + urgency share + negative context",
            "",
            "Highest pressure work types:",
        ]
    )
    for p in top_pressure:
        md_lines.append(
            f"- {p['work_type']}: pressure={p['execution_pressure_score']}, count={p['action_item_count']}, functions={p['dominant_functions']}"
        )

    md_lines.extend(
        [
            "",
            "## 3) Cross-functional friction map",
            "Method:",
            "- Detect disagreement/tension markers in summary + transcript",
            "- Blend discourse markers with negative sentiment into friction score",
            "- Aggregate by topic and call type",
            "",
            "Highest-friction meetings:",
        ]
    )
    for f in top_friction[:8]:
        md_lines.append(
            f"- {f['meeting_id']} | {f['call_type']} | {f['final_topic']} | friction={f['friction_score']} | speakers={f['top_friction_speakers']}"
        )

    md_lines.extend(
        [
            "",
            "## Why this matters",
            "- Risk scoring helps revenue and support leaders prioritize accounts before churn manifests.",
            "- Execution pressure identifies repeating operational burdens that can stall sentiment recovery.",
            "- Friction mapping shows where alignment breaks down across teams and call contexts.",
        ]
    )

    insights_md = args.output_dir / "business_insights_phase5.md"
    insights_md.write_text("\n".join(md_lines), encoding="utf-8")

    readme = args.output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Phase 5 - Additional Insights",
                "",
                "Script:",
                "- interview-assignment/scripts/build_phase5_additional_insights.py",
                "",
                "Outputs:",
                "- churn_risk_scores.csv",
                "- churn_risk_summary.csv",
                "- action_item_catalog.csv",
                "- action_item_execution_pressure.csv",
                "- cross_functional_friction_meetings.csv",
                "- cross_functional_friction_map.csv",
                "- business_insights_phase5.md",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote: {churn_csv}")
    print(f"Wrote: {summary_csv}")
    print(f"Wrote: {catalog_csv}")
    print(f"Wrote: {pressure_csv}")
    print(f"Wrote: {friction_meeting_csv}")
    print(f"Wrote: {friction_map_csv}")
    print(f"Wrote: {insights_md}")
    print(f"Wrote: {readme}")


if __name__ == "__main__":
    main()
