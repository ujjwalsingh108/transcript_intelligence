#!/usr/bin/env python3
"""Phase 2: deterministic call-type labeling with confidence and ambiguity handling.

Inputs:
- interview-assignment/outputs/phase1/meetings_flattened.csv
- interview-assignment/dataset/<meeting_id>/meeting-info.json
- interview-assignment/dataset/<meeting_id>/summary.json

Outputs:
- interview-assignment/outputs/phase2/meetings_call_types.csv
- interview-assignment/outputs/phase2/ambiguous_review.csv
- interview-assignment/outputs/phase2/labeling_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ACTIONS = {"support": "support", "external": "external", "internal": "internal", "ambiguous": "ambiguous"}


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def tokenize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def normalize_domains(domain_str: str) -> list[str]:
    if not domain_str:
        return []
    return sorted(set(d.strip().lower() for d in domain_str.split(";") if d.strip()))


def score_and_label(
    title: str,
    domains: list[str],
    topics: list[str],
    summary_text: str,
) -> dict[str, Any]:
    """Apply deterministic rule scoring and return label + confidence + evidence."""
    title_norm = tokenize(title)
    topic_blob = tokenize(" ".join(topics))
    text_blob = tokenize(" ".join([title, " ".join(topics), summary_text]))

    scores = Counter({"support": 0.0, "external": 0.0, "internal": 0.0})
    fired: list[str] = []

    # Domain signals
    domain_count = len(domains)
    if domain_count >= 2:
        scores["external"] += 2.0
        fired.append("R_DOMAIN_MULTI->external+2.0")
    if domain_count == 1:
        scores["internal"] += 1.5
        fired.append("R_DOMAIN_SINGLE->internal+1.5")

    # Title-first strong rules
    if re.match(r"^support case\s*#?\d+", title_norm):
        scores["support"] += 5.0
        fired.append("R_TITLE_SUPPORT_CASE->support+5.0")

    if re.match(r"^aegis\s*/", title_norm):
        scores["external"] += 4.0
        fired.append("R_TITLE_AEGIS_SLASH->external+4.0")

    if has_any(title_norm, [r"\binternal\b"]):
        scores["internal"] += 3.5
        fired.append("R_TITLE_INTERNAL->internal+3.5")

    # Support language
    support_blob = tokenize(" ".join([title, " ".join(topics)]))
    if has_any(
        support_blob,
        [
            r"^support case\s*#?\d+",
            r"\burgent\b",
            r"\boutage\b",
            r"\bincident\b",
            r"\bticket\b",
            r"\bcase\b",
            r"\bescalation\b",
            r"\btroubleshoot|troubleshooting\b",
            r"\blatency\b",
            r"\berror\b",
            r"\bbug\b",
            r"\brestore\b",
            r"\bfailure\b",
            r"\bsla breach\b",
            r"\bdegradation\b",
        ],
    ):
        scores["support"] += 1.8
        fired.append("R_SUPPORT_INCIDENT_LANGUAGE->support+1.8")

    # External/customer/account language
    external_blob = tokenize(" ".join([title, " ".join(topics)]))
    if has_any(
        external_blob,
        [
            r"\bcustomer\b",
            r"\brenewal\b",
            r"\bcontract\b",
            r"\baccount\b",
            r"\bpricing\b",
            r"\bupsell\b",
            r"\bcompetitive\b",
            r"\bchurn\b",
            r"\bhealth check\b",
            r"\bservice credits?\b",
            r"\bqbr\b",
        ],
    ):
        scores["external"] += 1.6
        fired.append("R_EXTERNAL_ACCOUNT_LANGUAGE->external+1.6")

    # Internal planning/team-process language
    internal_blob = tokenize(" ".join([title, " ".join(topics)]))
    if has_any(
        internal_blob,
        [
            r"\bstandup\b",
            r"\broadmap\b",
            r"\bsync\b",
            r"\bretro|retrospective\b",
            r"\bsprint\b",
            r"\bplanning\b",
            r"\blaunch readiness\b",
            r"\bpost\-incident review\b",
            r"\bwar room\b",
            r"\bteam\b",
            r"\bengineering\b",
        ],
    ):
        scores["internal"] += 1.8
        fired.append("R_INTERNAL_PLANNING_LANGUAGE->internal+1.8")

    # Tie-break nudges from topics only
    if has_any(topic_blob, [r"customer communication", r"customer retention", r"renewal", r"contract"]):
        scores["external"] += 0.6
        fired.append("R_TOPIC_EXTERNAL_HINT->external+0.6")

    if has_any(topic_blob, [r"sprint", r"roadmap", r"post\-mortem", r"runbook", r"resource allocation"]):
        scores["internal"] += 0.6
        fired.append("R_TOPIC_INTERNAL_HINT->internal+0.6")

    if has_any(topic_blob, [r"support", r"incident response", r"technical issue", r"backup", r"restore"]):
        scores["support"] += 0.6
        fired.append("R_TOPIC_SUPPORT_HINT->support+0.6")

    top_label, top_score = max(scores.items(), key=lambda kv: kv[1])
    second_score = sorted(scores.values(), reverse=True)[1]
    margin = round(top_score - second_score, 3)
    total = round(sum(scores.values()), 3)

    # Ambiguity criteria keeps us honest and reviewable.
    ambiguous = False
    reasons = []
    if top_score < 3.0:
        ambiguous = True
        reasons.append("low_top_score")
    if margin < 1.0:
        ambiguous = True
        reasons.append("low_margin")

    final_label = "ambiguous" if ambiguous else top_label

    # Confidence: bounded score from top score and separation margin.
    conf = min(0.99, max(0.35, 0.45 + 0.07 * top_score + 0.12 * min(margin, 3.0)))
    if ambiguous:
        conf = min(conf, 0.6)
    confidence = round(conf, 3)

    return {
        "label": final_label,
        "confidence": confidence,
        "raw_top_label": top_label,
        "score_support": round(scores["support"], 3),
        "score_external": round(scores["external"], 3),
        "score_internal": round(scores["internal"], 3),
        "score_total": total,
        "score_margin": margin,
        "ambiguous_reasons": ";".join(reasons),
        "rules_fired": "|".join(fired),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 deterministic call-type labeling")
    parser.add_argument(
        "--phase1-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase1/meetings_flattened.csv"),
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("interview-assignment/dataset"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase2/meetings_call_types.csv"),
    )
    parser.add_argument(
        "--ambiguous-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase2/ambiguous_review.csv"),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("interview-assignment/outputs/phase2/labeling_report.json"),
    )
    args = parser.parse_args()

    if not args.phase1_csv.exists():
        raise FileNotFoundError(f"Missing phase 1 csv: {args.phase1_csv}")

    rows: list[dict[str, Any]] = []
    with args.phase1_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    labeled_rows: list[dict[str, Any]] = []
    ambiguous_rows: list[dict[str, Any]] = []

    for row in rows:
        meeting_id = row["meeting_id"]
        title = row.get("title", "") or ""
        domains = normalize_domains(row.get("email_domains", "") or "")
        topics = [t.strip() for t in (row.get("summary_topics", "") or "").split(";") if t.strip()]

        summary_json = read_json(args.dataset_dir / meeting_id / "summary.json") or {}
        summary_text = str(summary_json.get("summary", "") or "")

        label_data = score_and_label(title=title, domains=domains, topics=topics, summary_text=summary_text)

        out = dict(row)
        out.update(
            {
                "call_type": label_data["label"],
                "call_type_confidence": label_data["confidence"],
                "raw_top_label": label_data["raw_top_label"],
                "score_support": label_data["score_support"],
                "score_external": label_data["score_external"],
                "score_internal": label_data["score_internal"],
                "score_total": label_data["score_total"],
                "score_margin": label_data["score_margin"],
                "ambiguous_reasons": label_data["ambiguous_reasons"],
                "rules_fired": label_data["rules_fired"],
            }
        )
        labeled_rows.append(out)

        if out["call_type"] == ACTIONS["ambiguous"]:
            ambiguous_rows.append(
                {
                    "meeting_id": meeting_id,
                    "title": title,
                    "email_domains": row.get("email_domains", ""),
                    "call_type_confidence": out["call_type_confidence"],
                    "raw_top_label": out["raw_top_label"],
                    "score_support": out["score_support"],
                    "score_external": out["score_external"],
                    "score_internal": out["score_internal"],
                    "score_margin": out["score_margin"],
                    "ambiguous_reasons": out["ambiguous_reasons"],
                    "rules_fired": out["rules_fired"],
                }
            )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Write full labeled table
    full_fields = list(labeled_rows[0].keys()) if labeled_rows else []
    with args.output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=full_fields)
        writer.writeheader()
        writer.writerows(labeled_rows)

    # Write ambiguity review subset
    amb_fields = [
        "meeting_id",
        "title",
        "email_domains",
        "call_type_confidence",
        "raw_top_label",
        "score_support",
        "score_external",
        "score_internal",
        "score_margin",
        "ambiguous_reasons",
        "rules_fired",
    ]
    with args.ambiguous_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=amb_fields)
        writer.writeheader()
        writer.writerows(ambiguous_rows)

    # Summary report
    label_counts = Counter(r["call_type"] for r in labeled_rows)
    report = {
        "meetings_total": len(labeled_rows),
        "label_counts": dict(label_counts),
        "ambiguous_count": label_counts.get("ambiguous", 0),
        "ambiguous_share": round(label_counts.get("ambiguous", 0) / len(labeled_rows), 4) if labeled_rows else 0.0,
        "confidence_summary": {
            "min": round(min((float(r["call_type_confidence"]) for r in labeled_rows), default=0.0), 3),
            "max": round(max((float(r["call_type_confidence"]) for r in labeled_rows), default=0.0), 3),
            "avg": round(
                sum(float(r["call_type_confidence"]) for r in labeled_rows) / len(labeled_rows),
                3,
            )
            if labeled_rows
            else 0.0,
        },
        "rules_note": "Deterministic weighted rules over title/domain/topics/summary with explicit ambiguity gating.",
    }
    args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote: {args.output_csv}")
    print(f"Wrote: {args.ambiguous_csv}")
    print(f"Wrote: {args.report_json}")
    print("Label counts:", dict(label_counts))


if __name__ == "__main__":
    main()
