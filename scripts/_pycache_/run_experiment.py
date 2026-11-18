#!/usr/bin/env python3
"""Run deterministic ranking comparisons on the frozen review bibliography."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import re
import sys
import time
from importlib.metadata import version
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.json"
CORPUS_PATH = ROOT / "data" / "reference_corpus.csv"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "paper" / "figures"
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "into", "is", "it",
    "of", "on", "or", "the", "their", "this", "to", "was", "what", "with", "within",
}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def minmax(values: dict[str, float]) -> dict[str, float]:
    low = min(values.values())
    high = max(values.values())
    if math.isclose(low, high):
        return {key: 0.0 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def bm25_scores(query: str, docs: dict[str, list[str]], k1: float, b: float) -> dict[str, float]:
    n_docs = len(docs)
    lengths = {doc_id: len(tokens) for doc_id, tokens in docs.items()}
    avgdl = sum(lengths.values()) / n_docs
    doc_freq = Counter(token for tokens in docs.values() for token in set(tokens))
    scores = {doc_id: 0.0 for doc_id in docs}
    for term in set(tokenize(query)):
        df = doc_freq[term]
        if not df:
            continue
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        for doc_id, tokens in docs.items():
            tf = tokens.count(term)
            if not tf:
                continue
            denominator = tf + k1 * (1 - b + b * lengths[doc_id] / avgdl)
            scores[doc_id] += idf * (tf * (k1 + 1)) / denominator
    return scores


def tfidf_scores(query: str, docs: dict[str, list[str]]) -> dict[str, float]:
    n_docs = len(docs)
    doc_freq = Counter(token for tokens in docs.values() for token in set(tokens))

    def vector(tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        weights = {
            token: (1 + math.log(count)) * (math.log((n_docs + 1) / (doc_freq[token] + 1)) + 1)
            for token, count in counts.items()
        }
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return {token: weight / norm for token, weight in weights.items()} if norm else {}

    query_vector = vector(tokenize(query))
    scores = {}
    for doc_id, tokens in docs.items():
        doc_vector = vector(tokens)
        scores[doc_id] = sum(value * doc_vector.get(token, 0.0) for token, value in query_vector.items())
    return scores


def rank_scores(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def dcg(relevant: list[str], ranked: list[str], k: int) -> float:
    return sum((1 / math.log2(rank + 1)) for rank, doc_id in enumerate(ranked[:k], 1) if doc_id in relevant)


def query_metrics(ranked: list[str], gold: set[str], low_gold: set[str], cites: dict[str, int], k: int) -> dict:
    top = ranked[:k]
    relevant_in_top = len(gold.intersection(top))
    first_relevant = next((i + 1 for i, doc_id in enumerate(ranked) if doc_id in gold), None)
    ideal = min(k, len(gold))
    ideal_dcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    low_recall = len(low_gold.intersection(top)) / len(low_gold) if low_gold else ""
    return {
        "recall_at_5": relevant_in_top / len(gold),
        "precision_at_5": relevant_in_top / k,
        "ndcg_at_5": dcg(gold, ranked, k) / ideal_dcg if ideal_dcg else 0.0,
        "mrr": 1 / first_relevant if first_relevant else 0.0,
        "low_citation_recall_at_5": low_recall,
        "mean_log_citations_top_5": sum(math.log1p(cites[doc_id]) for doc_id in top) / k,
        "top_5_ref_ids": ";".join(top),
    }


def fmt(value) -> str:
    if value == "":
        return ""
    return f"{value:.6f}" if isinstance(value, float) else str(value)


def save_plot(summary: list[dict], sensitivity: list[dict]) -> None:
    method_order = ["BM25", "TF-IDF", "BM25+Citation (lambda=0.25)"]
    by_method = {row["method"]: row for row in summary}
    values = [float(by_method[name]["macro_recall_at_5"]) for name in method_order]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bars = ax.bar(method_order, values, color=["#64748b", "#0f766e", "#c2410c"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Macro Recall@5")
    ax.set_title("Retrieval of review-annotated references (15-work corpus)")
    ax.grid(axis="y", alpha=0.25)
    ax.bar_label(bars, fmt="%.3f", padding=3)
    ax.tick_params(axis="x", rotation=10)
    fig.tight_layout()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(RESULTS_DIR / "recall_at_5.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "recall_at_5.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    lambdas = [float(row["lambda"]) for row in sensitivity]
    low_recall = [float(row["macro_low_citation_recall_at_5"]) for row in sensitivity]
    top_cites = [float(row["mean_log_citations_top_5"]) for row in sensitivity]
    fig, left = plt.subplots(figsize=(7.2, 4.2))
    left.plot(lambdas, low_recall, marker="o", color="#0f766e", label="Low-citation Recall@5")
    left.set_xlabel("Citation prior weight (lambda)")
    left.set_ylabel("Macro low-citation Recall@5", color="#0f766e")
    left.set_ylim(0, 1)
    left.grid(alpha=0.25)
    right = left.twinx()
    right.plot(lambdas, top_cites, marker="s", color="#c2410c", label="Mean log citations in top 5")
    right.set_ylabel("Mean log1p citations in top 5", color="#c2410c")
    left.set_title("Sensitivity to citation-prior weight")
    lines = left.get_lines() + right.get_lines()
    left.legend(lines, [line.get_label() for line in lines], loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "citation_sensitivity.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "citation_sensitivity.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    run_started = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    corpus = read_csv(CORPUS_PATH)
    if len(corpus) != 15 or len({row["ref_id"] for row in corpus}) != 15:
        raise ValueError("Expected exactly 15 unique corpus records (R01-R15).")
    refs = {row["ref_id"]: row for row in corpus}
    if set(refs) != {f"R{i:02d}" for i in range(1, 16)}:
        raise ValueError("Reference IDs must be the complete set R01-R15.")
    for row in corpus:
        if row["abstract_missing"] not in {"true", "false"}:
            raise ValueError(f"Missing/invalid abstract marker for {row['ref_id']}.")
    if len([r for r in corpus if r["abstract_missing"] == "true"]) != 1:
        raise ValueError("The frozen protocol expects one title-only document.")

    gold_labels = []
    for query in config["queries"]:
        gold = set(query["gold_ref_ids"])
        if not gold or not gold.issubset(refs):
            raise ValueError(f"Invalid gold labels for {query['query_id']}.")
        for doc_id in refs:
            gold_labels.append({
                "query_id": query["query_id"],
                "ref_id": doc_id,
                "relevant": int(doc_id in gold),
                "annotation_basis": query["annotation_basis"] if doc_id in gold else "Not in the query-specific relevant set frozen in experiment.json.",
            })
    write_csv(ROOT / "data" / "gold_labels.csv", gold_labels, ["query_id", "ref_id", "relevant", "annotation_basis"])

    citation_counts = {doc_id: int(row["cited_by_count"] or 0) for doc_id, row in refs.items()}
    citation_order = sorted(refs, key=lambda doc_id: (citation_counts[doc_id], doc_id))
    n = len(citation_order)
    strata = {}
    for rank, doc_id in enumerate(citation_order):
        strata[doc_id] = "low" if rank < n // 3 else "medium" if rank < 2 * n // 3 else "high"
    low_ids = {doc_id for doc_id, stratum in strata.items() if stratum == "low"}
    docs = {
        doc_id: tokenize((row["openalex_title"] or row["bibliography_title"]) + " " + row["abstract"])
        for doc_id, row in refs.items()
    }

    k = int(config["k"])
    lambda_values = [float(x) for x in config["citation_prior"]["sensitivity_lambdas"]]
    primary_lambda = float(config["citation_prior"]["primary_lambda"])
    citation_prior = minmax({doc_id: math.log1p(citation_counts[doc_id]) for doc_id in refs})
    query_metrics_rows = []
    ranking_rows = []
    sensitivity_rows = []
    query_scores_cache = {}

    for query in config["queries"]:
        query_id = query["query_id"]
        gold = set(query["gold_ref_ids"])
        low_gold = gold.intersection(low_ids)
        bm25 = bm25_scores(query["text"], docs, float(config["bm25"]["k1"]), float(config["bm25"]["b"]))
        tfidf = tfidf_scores(query["text"], docs)
        bm25_norm = minmax(bm25)
        hybrid_scores = {
            doc_id: (1 - primary_lambda) * bm25_norm[doc_id] + primary_lambda * citation_prior[doc_id]
            for doc_id in refs
        }
        method_scores = {
            "BM25": bm25,
            "TF-IDF": tfidf,
            f"BM25+Citation (lambda={primary_lambda:.2f})": hybrid_scores,
        }
        query_scores_cache[query_id] = (bm25, bm25_norm, tfidf, gold, low_gold)

        for method, scores in method_scores.items():
            ranked = rank_scores(scores)
            metrics = query_metrics(ranked, gold, low_gold, citation_counts, k)
            row = {"query_id": query_id, "method": method, **metrics}
            query_metrics_rows.append({key: fmt(value) for key, value in row.items()})
            for position, doc_id in enumerate(ranked, 1):
                ranking_rows.append({
                    "query_id": query_id,
                    "method": method,
                    "rank": position,
                    "ref_id": doc_id,
                    "score": fmt(scores[doc_id]),
                    "relevant": int(doc_id in gold),
                    "citation_stratum": strata[doc_id],
                    "cited_by_count": citation_counts[doc_id],
                })

        for weight in lambda_values:
            scores = {
                doc_id: (1 - weight) * bm25_norm[doc_id] + weight * citation_prior[doc_id]
                for doc_id in refs
            }
            ranked = rank_scores(scores)
            if math.isclose(weight, 0.0) and ranked != rank_scores(bm25):
                raise AssertionError("lambda=0 must reproduce the BM25 ranking exactly.")
            if math.isclose(weight, 1.0) and ranked != rank_scores(citation_prior):
                raise AssertionError("lambda=1 must reproduce the citation-prior ranking exactly.")
            if len(ranked) != len(refs) or len(set(ranked)) != len(refs):
                raise AssertionError("Every sensitivity ranking must contain each corpus record once.")
            metrics = query_metrics(ranked, gold, low_gold, citation_counts, k)
            for metric in ("recall_at_5", "precision_at_5", "ndcg_at_5", "mrr", "low_citation_recall_at_5"):
                value = metrics[metric]
                if value != "" and not 0.0 <= float(value) <= 1.0:
                    raise AssertionError(f"Metric {metric} is outside [0, 1]: {value}")
            sensitivity_rows.append({"query_id": query_id, "lambda": fmt(weight), **{key: fmt(value) for key, value in metrics.items()}})

    metric_names = ["recall_at_5", "precision_at_5", "ndcg_at_5", "mrr", "low_citation_recall_at_5", "mean_log_citations_top_5"]
    summary_rows = []
    for method in ["BM25", "TF-IDF", f"BM25+Citation (lambda={primary_lambda:.2f})"]:
        subset = [row for row in query_metrics_rows if row["method"] == method]
        summary = {"method": method}
        for metric in metric_names:
            values = [float(row[metric]) for row in subset if row[metric] != ""]
            summary[f"macro_{metric}"] = fmt(sum(values) / len(values))
        summary["queries_n"] = len(subset)
        summary_rows.append(summary)

    sensitivity_summary = []
    for weight in lambda_values:
        subset = [row for row in sensitivity_rows if float(row["lambda"]) == weight]
        recall_values = [float(row["recall_at_5"]) for row in subset]
        low_values = [float(row["low_citation_recall_at_5"]) for row in subset if row["low_citation_recall_at_5"] != ""]
        citation_values = [float(row["mean_log_citations_top_5"]) for row in subset]
        sensitivity_summary.append({
            "lambda": fmt(weight),
            "macro_recall_at_5": fmt(sum(recall_values) / len(recall_values)),
            "macro_low_citation_recall_at_5": fmt(sum(low_values) / len(low_values)),
            "mean_log_citations_top_5": fmt(sum(citation_values) / len(citation_values)),
        })

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS_DIR / "query_metrics.csv", query_metrics_rows, list(query_metrics_rows[0]))
    write_csv(RESULTS_DIR / "metrics_summary.csv", summary_rows, list(summary_rows[0]))
    write_csv(RESULTS_DIR / "rankings.csv", ranking_rows, list(ranking_rows[0]))
    write_csv(RESULTS_DIR / "sensitivity.csv", sensitivity_rows, list(sensitivity_rows[0]))
    write_csv(RESULTS_DIR / "sensitivity_summary.csv", sensitivity_summary, list(sensitivity_summary[0]))
    save_plot(summary_rows, sensitivity_summary)

    corpus_hash = hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    config_hash = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
    metadata = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_type": "deterministic; no random seed used",
        "elapsed_seconds": round(time.perf_counter() - run_started, 4),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "matplotlib": version("matplotlib"),
        },
        "corpus_path": CORPUS_PATH.relative_to(ROOT).as_posix(),
        "corpus_sha256": corpus_hash,
        "config_sha256": config_hash,
        "script_sha256": script_hash,
        "n_documents": len(refs),
        "n_queries": len(config["queries"]),
        "n_gold_labels": sum(len(query["gold_ref_ids"]) for query in config["queries"]),
        "abstract_missing": [row["ref_id"] for row in corpus if row["abstract_missing"] == "true"],
        "citation_strata": {name: sorted(doc_id for doc_id, value in strata.items() if value == name) for name in ["low", "medium", "high"]},
        "primary_lambda": primary_lambda,
        "sensitivity_lambdas": lambda_values,
        "metrics_summary": summary_rows,
        "sensitivity_summary": sensitivity_summary,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Ran {len(config['queries'])} queries over {len(corpus)} records; K={k}; primary lambda={primary_lambda}.")
    for row in summary_rows:
        print(row)
    print(f"Wrote result CSVs and figures to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
