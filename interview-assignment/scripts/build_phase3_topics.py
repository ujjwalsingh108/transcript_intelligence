#!/usr/bin/env python3
"""Phase 3: hybrid topic/theme categorization pipeline.

Step A: Unsupervised theme discovery (custom TF-IDF + NumPy KMeans).
Step B: Assisted naming of clusters (rule-assisted naming from cluster terms/titles).
Step C: Rule refinement for edge cases (meeting-level overrides).

Outputs:
- interview-assignment/outputs/phase3/meetings_with_topics.csv
- interview-assignment/outputs/phase3/topic_taxonomy.json
- interview-assignment/outputs/phase3/topic_counts_by_call_type.csv
- interview-assignment/outputs/phase3/topic_representative_snippets.csv
- interview-assignment/outputs/phase3/cluster_diagnostics.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "s",
    "so",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "up",
    "was",
    "we",
    "what",
    "when",
    "with",
    "you",
    "your",
    "ll",
    "ve",
    "re",
    "t",
    "d",
    "m",
}

TOPIC_KEYWORDS = {
    "Incident Response & Outage Management": [
        "outage",
        "incident",
        "failure",
        "war",
        "bridge",
        "postmortem",
        "remediation",
    ],
    "Support Troubleshooting & Case Resolution": [
        "support",
        "ticket",
        "case",
        "troubleshooting",
        "latency",
        "bug",
        "error",
        "restore",
    ],
    "Compliance & Audit Readiness": [
        "compliance",
        "audit",
        "soc",
        "iso",
        "hipaa",
        "pci",
        "evidence",
    ],
    "Renewal, Pricing & Commercial Negotiation": [
        "renewal",
        "pricing",
        "contract",
        "quote",
        "discount",
        "overage",
        "billing",
    ],
    "Identity, Access & Provisioning": [
        "identity",
        "access",
        "mfa",
        "scim",
        "provisioning",
        "sso",
        "rbac",
    ],
    "Product Roadmap & Engineering Execution": [
        "roadmap",
        "standup",
        "sprint",
        "planning",
        "launch",
        "retro",
        "team",
    ],
    "Security Monitoring & Threat Detection": [
        "threat",
        "detect",
        "monitoring",
        "alert",
        "detection",
        "security",
    ],
    "Customer Retention & Escalation Risk": [
        "churn",
        "escalation",
        "risk",
        "customer",
        "pushback",
        "retention",
    ],
    "Platform Reliability & Performance": [
        "reliability",
        "performance",
        "pipeline",
        "scalability",
        "throughput",
        "degradation",
    ],
}


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]


def build_vocabulary(tokenized_docs: list[list[str]], min_df: int, max_features: int) -> list[str]:
    doc_freq = Counter()
    for toks in tokenized_docs:
        doc_freq.update(set(toks))

    vocab_items = [(tok, df) for tok, df in doc_freq.items() if df >= min_df]
    vocab_items.sort(key=lambda x: (-x[1], x[0]))
    vocab = [tok for tok, _ in vocab_items[:max_features]]
    return vocab


def tfidf_matrix(tokenized_docs: list[list[str]], vocab: list[str]) -> np.ndarray:
    if not tokenized_docs or not vocab:
        return np.zeros((len(tokenized_docs), 0), dtype=np.float64)

    term_index = {t: i for i, t in enumerate(vocab)}
    n_docs = len(tokenized_docs)
    n_terms = len(vocab)

    tf = np.zeros((n_docs, n_terms), dtype=np.float64)
    df = np.zeros(n_terms, dtype=np.float64)

    for i, toks in enumerate(tokenized_docs):
        counts = Counter(t for t in toks if t in term_index)
        if not counts:
            continue
        total = sum(counts.values())
        for term, c in counts.items():
            j = term_index[term]
            tf[i, j] = c / total
        for term in counts:
            df[term_index[term]] += 1.0

    idf = np.log((1.0 + n_docs) / (1.0 + df)) + 1.0
    x = tf * idf

    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


def kmeans(x: np.ndarray, k: int, seed: int = 42, max_iter: int = 60) -> tuple[np.ndarray, np.ndarray]:
    """Simple KMeans with deterministic seed and cosine-friendly normalized vectors."""
    n = x.shape[0]
    if n == 0:
        return np.array([], dtype=int), np.zeros((0, x.shape[1]))

    rng = np.random.default_rng(seed)
    k = max(2, min(k, n))

    # KMeans++ style init.
    centroids = np.zeros((k, x.shape[1]), dtype=np.float64)
    first = rng.integers(0, n)
    centroids[0] = x[first]

    closest_dist_sq = np.sum((x - centroids[0]) ** 2, axis=1)
    for c in range(1, k):
        probs = closest_dist_sq / (closest_dist_sq.sum() + 1e-12)
        idx = rng.choice(n, p=probs)
        centroids[c] = x[idx]
        new_dist_sq = np.sum((x - centroids[c]) ** 2, axis=1)
        closest_dist_sq = np.minimum(closest_dist_sq, new_dist_sq)

    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        # Assign
        dists = np.stack([np.sum((x - centroids[c]) ** 2, axis=1) for c in range(k)], axis=1)
        new_labels = np.argmin(dists, axis=1)

        if np.array_equal(new_labels, labels):
            break
        labels = new_labels

        # Update
        for c in range(k):
            members = x[labels == c]
            if len(members) == 0:
                centroids[c] = x[rng.integers(0, n)]
            else:
                centroid = members.mean(axis=0)
                norm = np.linalg.norm(centroid)
                centroids[c] = centroid / norm if norm else centroid

    return labels, centroids


def top_terms_for_cluster(centroids: np.ndarray, vocab: list[str], cluster_id: int, top_n: int = 12) -> list[str]:
    if centroids.size == 0:
        return []
    w = centroids[cluster_id]
    idx = np.argsort(-w)[:top_n]
    return [vocab[i] for i in idx if w[i] > 0]


def choose_topic_name(top_terms: list[str], sample_titles: list[str]) -> tuple[str, dict[str, int]]:
    """Step B: assisted naming using keyword scoring against discovered cluster signals."""
    blob = " ".join(top_terms + [t.lower() for t in sample_titles])
    scores: dict[str, int] = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        scores[topic] = sum(1 for kw in kws if kw in blob)

    best_topic = max(scores.items(), key=lambda kv: kv[1])[0]
    if scores[best_topic] == 0:
        fallback = " / ".join(top_terms[:3]) if top_terms else "General"
        return f"Uncategorized: {fallback}", scores
    return best_topic, scores


def refine_topic(initial_topic: str, title: str, summary_topics: str, call_type: str) -> str:
    """Step C: deterministic edge-case refinement rules."""
    blob = f"{title} {summary_topics}".lower()

    if re.search(r"support case\s*#|ticket|troubleshoot|restore|bug|latency", blob):
        return "Support Troubleshooting & Case Resolution"

    if re.search(r"soc\s*2|iso\s*27001|hipaa|pci|audit|compliance reporting|multi-framework|attestation", blob):
        return "Compliance & Audit Readiness"

    if re.search(r"identity|access|mfa|scim|provisioning|sso|rbac", blob):
        return "Identity, Access & Provisioning"

    if re.search(r"outage|war room|post-incident|escalation bridge|pipeline failure|complete loss", blob):
        return "Incident Response & Outage Management"

    if re.search(r"incident response|incident review|incident postmortem", blob):
        return "Incident Response & Outage Management"

    if re.search(r"renewal|pricing|contract|billing|overage|discount", blob):
        return "Renewal, Pricing & Commercial Negotiation"

    if re.search(r"standup|roadmap|sprint|planning|retro|launch readiness", blob):
        return "Product Roadmap & Engineering Execution"

    if re.search(r"threat|detect|monitoring|detection|alert", blob):
        return "Security Monitoring & Threat Detection"

    if call_type == "external" and re.search(r"churn|escalation|risk|pushback", blob):
        return "Customer Retention & Escalation Risk"

    if re.search(r"reliability|performance|pipeline|scalability|throughput", blob):
        return "Platform Reliability & Performance"

    return initial_topic


def informative_sentences(transcript_json: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not transcript_json:
        return []
    rows = transcript_json.get("data")
    if not isinstance(rows, list):
        return []

    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        s = str(r.get("sentence", "")).strip()
        if len(s) < 45:
            continue
        if re.search(r"\b(hello|hi|can you hear me|thanks|thank you|bye)\b", s.lower()):
            continue

        tokens = tokenize(s)
        info_score = len(set(tokens)) + 0.15 * len(tokens)
        out.append(
            {
                "text": s,
                "speaker": r.get("speaker_name", ""),
                "time": r.get("time", ""),
                "score": round(info_score, 3),
            }
        )

    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 hybrid topic categorization")
    parser.add_argument(
        "--phase2-csv",
        type=Path,
        default=Path("interview-assignment/outputs/phase2/meetings_call_types.csv"),
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("interview-assignment/dataset"),
    )
    parser.add_argument(
        "--k",
        type=int,
        default=9,
        help="Number of unsupervised clusters (recommended 6-12).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("interview-assignment/outputs/phase3"),
    )
    args = parser.parse_args()

    rows = list(csv.DictReader(args.phase2_csv.open("r", encoding="utf-8", newline="")))

    enriched = []
    tokenized_docs = []

    for row in rows:
        mid = row["meeting_id"]
        summary_json = read_json(args.dataset_dir / mid / "summary.json") or {}

        summary_text = str(summary_json.get("summary", "") or "")
        action_items = summary_json.get("actionItems", [])
        if not isinstance(action_items, list):
            action_items = []
        key_moments = summary_json.get("keyMoments", [])
        if not isinstance(key_moments, list):
            key_moments = []

        key_moment_text = " ".join(str(k.get("text", "")) for k in key_moments if isinstance(k, dict))
        doc = " ".join(
            [
                row.get("title", "") or "",
                row.get("summary_topics", "") or "",
                summary_text,
                " ".join(str(x) for x in action_items),
                key_moment_text,
            ]
        )

        toks = tokenize(doc)
        tokenized_docs.append(toks)

        enriched.append(
            {
                **row,
                "summary_text": summary_text,
                "document_text": doc,
            }
        )

    vocab = build_vocabulary(tokenized_docs, min_df=2, max_features=2000)
    x = tfidf_matrix(tokenized_docs, vocab)

    labels, centroids = kmeans(x, k=args.k, seed=42)

    # Cluster diagnostics + assisted naming
    cluster_info: dict[int, dict[str, Any]] = {}
    for cid in sorted(set(int(l) for l in labels.tolist())):
        member_idx = [i for i, l in enumerate(labels.tolist()) if int(l) == cid]
        top_terms = top_terms_for_cluster(centroids, vocab, cid, top_n=12)
        sample_titles = [enriched[i]["title"] for i in member_idx[:5]]
        name, name_scores = choose_topic_name(top_terms, sample_titles)

        cluster_info[cid] = {
            "cluster_id": cid,
            "size": len(member_idx),
            "top_terms": top_terms,
            "sample_titles": sample_titles,
            "assisted_name": name,
            "name_match_scores": name_scores,
        }

    # Meeting-level assignment and refinement
    for i, row in enumerate(enriched):
        cid = int(labels[i]) if len(labels) else -1
        assisted_name = cluster_info[cid]["assisted_name"] if cid in cluster_info else "Uncategorized"
        final_topic = refine_topic(
            assisted_name,
            title=row.get("title", "") or "",
            summary_topics=row.get("summary_topics", "") or "",
            call_type=row.get("call_type", "") or "",
        )

        row["cluster_id"] = cid
        row["cluster_assisted_name"] = assisted_name
        row["final_topic"] = final_topic

    # Final taxonomy
    topic_counts = Counter(r["final_topic"] for r in enriched)
    taxonomy = sorted(topic_counts.keys())

    # Counts by call type
    call_types = sorted(set(r["call_type"] for r in enriched))
    topic_call_counts: dict[str, dict[str, int]] = {
        t: {ct: 0 for ct in call_types} for t in taxonomy
    }
    for r in enriched:
        topic_call_counts[r["final_topic"]][r["call_type"]] += 1

    # Representative snippets: 2-3 per topic
    snippets_out = []
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in enriched:
        by_topic[r["final_topic"]].append(r)

    for topic in taxonomy:
        candidates = []
        topic_rows = by_topic[topic]

        # Prefer diverse meetings for representativeness.
        for r in topic_rows:
            mid = r["meeting_id"]
            transcript_json = read_json(args.dataset_dir / mid / "transcript.json")
            for s in informative_sentences(transcript_json)[:5]:
                candidates.append(
                    {
                        "meeting_id": mid,
                        "title": r.get("title", ""),
                        "call_type": r.get("call_type", ""),
                        "speaker_name": s["speaker"],
                        "time_sec": s["time"],
                        "snippet": s["text"],
                        "score": s["score"],
                    }
                )

        # Simple redundancy control by text prefix.
        seen_prefix = set()
        chosen = []
        for c in sorted(candidates, key=lambda x: x["score"], reverse=True):
            prefix = c["snippet"][:55].lower()
            if prefix in seen_prefix:
                continue
            seen_prefix.add(prefix)
            chosen.append(c)
            if len(chosen) == 3:
                break

        for c in chosen:
            snippets_out.append({"topic": topic, **c})

    # Persist outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)

    meetings_out = args.output_dir / "meetings_with_topics.csv"
    meetings_fields = [
        "meeting_id",
        "title",
        "call_type",
        "call_type_confidence",
        "cluster_id",
        "cluster_assisted_name",
        "final_topic",
        "summary_topics",
        "overall_sentiment",
        "sentiment_score",
    ]
    with meetings_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=meetings_fields)
        w.writeheader()
        for r in enriched:
            w.writerow({k: r.get(k, "") for k in meetings_fields})

    counts_out = args.output_dir / "topic_counts_by_call_type.csv"
    count_fields = ["topic", "total"] + call_types
    with counts_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=count_fields)
        w.writeheader()
        for topic in taxonomy:
            row = {"topic": topic, "total": topic_counts[topic]}
            row.update(topic_call_counts[topic])
            w.writerow(row)

    snippets_csv = args.output_dir / "topic_representative_snippets.csv"
    snippet_fields = [
        "topic",
        "meeting_id",
        "title",
        "call_type",
        "speaker_name",
        "time_sec",
        "snippet",
        "score",
    ]
    with snippets_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=snippet_fields)
        w.writeheader()
        for s in snippets_out:
            w.writerow(s)

    taxonomy_json = args.output_dir / "topic_taxonomy.json"
    taxonomy_json.write_text(
        json.dumps(
            {
                "topics": taxonomy,
                "topic_count": len(taxonomy),
                "topic_sizes": dict(topic_counts),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    diagnostics_json = args.output_dir / "cluster_diagnostics.json"
    diagnostics_json.write_text(
        json.dumps(
            {
                "k": args.k,
                "vocab_size": len(vocab),
                "clusters": cluster_info,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote: {meetings_out}")
    print(f"Wrote: {taxonomy_json}")
    print(f"Wrote: {counts_out}")
    print(f"Wrote: {snippets_csv}")
    print(f"Wrote: {diagnostics_json}")
    print(f"Final taxonomy topics: {len(taxonomy)}")


if __name__ == "__main__":
    main()
