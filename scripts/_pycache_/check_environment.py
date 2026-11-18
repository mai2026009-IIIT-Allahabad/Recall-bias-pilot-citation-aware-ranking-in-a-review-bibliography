#!/usr/bin/env python3
"""Run the project's small local environment and ranker sanity check."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import matplotlib
import reportlab
from run_experiment import bm25_scores, rank_scores, tfidf_scores, tokenize


def main() -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError(f"Python 3.10+ is required; found {sys.version.split()[0]}.")

    docs = {
        "review_match": tokenize("systematic review literature screening"),
        "control": tokenize("solar photosynthesis plant growth"),
    }
    query = "literature screening systematic review"
    bm25_rank = rank_scores(bm25_scores(query, docs, k1=1.5, b=0.75))
    tfidf_rank = rank_scores(tfidf_scores(query, docs))
    if bm25_rank[0] != "review_match" or tfidf_rank[0] != "review_match":
        raise AssertionError("Ranker smoke check failed: the topical match must rank first.")

    report = {
        "status": "PASS",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "matplotlib": version("matplotlib"),
        "reportlab": version("reportlab"),
        "checks": {
            "python_minimum": "passed",
            "matplotlib_import": "passed",
            "reportlab_import": "passed",
            "bm25_topical_smoke": bm25_rank[0],
            "tfidf_topical_smoke": tfidf_rank[0],
        },
        "gpu": "not required; rankers run on CPU",
    }
    output = ROOT / "results" / "environment_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: Python, matplotlib, ReportLab, BM25, and TF-IDF environment checks.")
    print(f"Python {report['python']}; matplotlib {report['matplotlib']}; reportlab {report['reportlab']}.")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
