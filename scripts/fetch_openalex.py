#!/usr/bin/env python3
"""Fetch OpenAlex metadata for the review's 15 cited works."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIELDS = (
    "id,doi,title,publication_year,cited_by_count,language,"
    "abstract_inverted_index,primary_location,authorships"
)
USER_AGENT = "RecallBiasPilot/1.0 (reproducible academic pilot)"

RECORDS = [
    ("R01", 1, "LitLLMs, LLMs for Literature Review: Are We There Yet?", "title", "LitLLMs, LLMs for Literature Review: Are We There Yet?", 2025),
    ("R02", 2, "Large Language Models Reflect Human Citation Patterns with a Heightened Citation Bias", "doi", "10.18653/v1/2025.findings-naacl.381", 2025),
    ("R03", 3, "Transforming Literature Screening: The Emerging Role of Large Language Models in Systematic Reviews", "doi", "10.1073/pnas.2411962122", 2025),
    ("R04", 4, "Evaluating Large Language Models for Radiology Systematic Review Title and Abstract Screening", "doi", "10.1016/j.acra.2025.08.014", 2025),
    ("R05", 5, "Exploratory Evaluation of Large Language Models for Reducing Language Bias in Systematic Review Screening", "doi", "10.3233/SHTI260813", 2026),
    ("R06", 6, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "doi", "10.48550/arxiv.2005.11401", 2020),
    ("R07", 7, "Human-Comparable Sensitivity of Large Language Models in Identifying Eligible Studies Through Title and Abstract Screening: 3-Layer Strategy Using GPT-3.5 and GPT-4 for Systematic Reviews", "doi", "10.2196/52758", 2024),
    ("R08", 8, "The Matthew Effect in Science: The Reward and Communication Systems of Science Are Considered", "doi", "10.1126/science.159.3810.56", 1968),
    ("R09", 9, "The Prevalence of and Factors Associated with Inclusion of Non-English Language Studies in Campbell Systematic Reviews: A Survey and Meta-Epidemiological Study", "doi", "10.1186/s13643-018-0786-6", 2018),
    ("R10", 10, "The PRISMA 2020 Statement: An Updated Guideline for Reporting Systematic Reviews", "doi", "10.1136/bmj.n71", 2021),
    ("R11", 11, "Test-time Corpus Feedback: From Retrieval to RAG", "doi", "10.18653/v1/2026.findings-eacl.298", 2026),
    ("R12", 12, "Addressing Linguistic Bias through a Contrastive Analysis of Academic Writing in the NLP Domain", "doi", "10.18653/v1/2023.emnlp-main.1042", 2023),
    ("R13", 13, "The Emergence of Large Language Models as Tools in Literature Reviews: A Large Language Model-Assisted Systematic Review", "doi", "10.1093/jamia/ocaf063", 2025),
    ("R14", 14, "Language Bias in Systematic Reviews: You Only Get Out What You Put In", "doi", "10.11124/JBIES-20-00361", 2020),
    ("R15", 15, "Who Gets Recommended? Investigating Gender, Race, and Country Disparities in Paper Recommendations from Large Language Models", "doi", "10.48550/arxiv.2501.00367", 2024),
]


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def reconstruct_abstract(index: dict | None) -> str:
    if not index:
        return ""
    max_position = max(position for positions in index.values() for position in positions)
    words = [""] * (max_position + 1)
    for word, positions in index.items():
        for position in positions:
            words[position] = word
    return " ".join(word for word in words if word)


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


def lookup(kind: str, key: str) -> tuple[dict, dict]:
    if kind == "doi":
        path = "works/https%3A%2F%2Fdoi.org%2F" + urllib.parse.quote(key, safe="")
        url = f"https://api.openalex.org/{path}?select={FIELDS}"
        payload = get_json(url)
        indexed_doi = (payload.get("doi") or "").rstrip("/").lower()
        requested_doi = f"https://doi.org/{key}".lower()
        if indexed_doi != requested_doi:
            raise ValueError(f"DOI mismatch for {key}: {payload.get('doi')}")
        return payload, payload

    query = urllib.parse.urlencode({"search": key, "per-page": 10, "select": FIELDS})
    url = f"https://api.openalex.org/works?{query}"
    payload = get_json(url)
    exact = [item for item in payload.get("results", []) if normalized_title(item.get("title", "")) == normalized_title(key)]
    if len(exact) != 1:
        raise ValueError(f"Expected one exact title match for {key!r}; found {len(exact)}")
    return exact[0], {"query_url": url, "matched_record": exact[0]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snapshot = {"source": "OpenAlex public API", "retrieved_at_utc": retrieved_at, "records": []}
    rows = []

    for ref_id, ref_num, source_title, lookup_kind, lookup_key, cited_year in RECORDS:
        record, response = lookup(lookup_kind, lookup_key)
        abstract = reconstruct_abstract(record.get("abstract_inverted_index"))
        rows.append({
            "ref_id": ref_id,
            "review_reference_number": ref_num,
            "bibliography_title": source_title,
            "openalex_title": record.get("title", ""),
            "publication_year_openalex": record.get("publication_year", ""),
            "year_as_cited_in_review": cited_year,
            "cited_by_count": record.get("cited_by_count", ""),
            "language": record.get("language", ""),
            "doi": record.get("doi", ""),
            "openalex_id": record.get("id", ""),
            "abstract": abstract,
            "abstract_missing": str(not bool(abstract)).lower(),
            "primary_landing_page": (record.get("primary_location") or {}).get("landing_page_url", ""),
        })
        snapshot["records"].append({"ref_id": ref_id, "response": response})
        time.sleep(0.12)

    csv_path = args.data_dir / "reference_corpus.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    snapshot_path = args.data_dir / "openalex_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(rows)} records to {csv_path}")
    print(f"Snapshot retrieved {retrieved_at} to {snapshot_path}")
    print(f"Records without abstracts: {sum(row['abstract_missing'] == 'true' for row in rows)}")


if __name__ == "__main__":
    main()
