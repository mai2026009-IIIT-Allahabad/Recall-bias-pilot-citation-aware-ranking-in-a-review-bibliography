# Recall-bias pilot: citation-aware ranking in a review bibliography

This repository contains a small, reproducible computational pilot derived from the supplied literature review, *Recall Bias Toward Highly Cited and English Language Papers in AI Literature Curation*. It evaluates a narrow ranking question on the 15 works in that review's reference list.

## Research question

For four review-grounded topic queries over the review's 15 cited works, how does adding an OpenAlex citation-count prior to BM25 affect Recall@5 for the manually annotated relevant references, especially the lowest-citation third of the corpus?

The pilot compares BM25, TF-IDF cosine similarity, and BM25 with a citation prior. It is a controlled ranking experiment, not an evaluation of an LLM, a general scholarly search engine, or recall over all literature in the field. The fixed corpus and labels are intentionally narrow; the limitations are documented in the paper and decision log.

## Project files

- `configs/experiment.json`: frozen queries, relevance labels, metric definitions, and ranking settings.
- `data/reference_corpus.csv`: OpenAlex snapshot used for the reported run.
- `data/gold_labels.csv`: expanded query/reference judgments generated from the frozen protocol.
- `scripts/fetch_openalex.py`: fetches and validates metadata for the 15 cited works.
- `scripts/check_environment.py`: verifies dependencies and performs a small lexical-ranking smoke check.
- `scripts/run_experiment.py`: runs the ranking comparison, checks inputs, and exports metrics and figures.
- `results/`: actual outputs from the run on the included snapshot.
- `paper/`: manuscript source, bibliography, and figures.
- `research_brief.md`: one-page Gate G1 brief.
- `research_decisions.md`, `baseline_validation.md`, `ai_assistance_log.md`: research provenance.
- `sources_checked.md`: primary-source and bibliographic metadata checks.
- `demo_script.md`: five-minute demonstration outline.

## Reproduce

Python 3.12.10 was used. Install the listed dependencies in `requirements.txt`.

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/check_environment.py
python scripts/run_experiment.py
```

To regenerate the paper PDF and LaTeX source after rerunning the experiment, run `python scripts/build_manuscript.py`. The PDF is a ReportLab reading build; `paper/main.tex` is the ACM-style Overleaf source.

The command above uses the included frozen `data/reference_corpus.csv` snapshot, so results do not depend on current citation counts. To retrieve a fresh snapshot from OpenAlex first, run:

```powershell
python scripts/fetch_openalex.py
python scripts/run_experiment.py
```

Fresh snapshots will change over time as citation counts and OpenAlex records change. Keep the fetched CSV and JSON response together with any new results. OpenAlex requests are public, unauthenticated API calls; the script records its retrieval time and source IDs.

## Main outputs

- `results/query_metrics.csv`: one metric row per query and method.
- `results/metrics_summary.csv`: unweighted descriptive macro averages across the four queries.
- `results/rankings.csv`: full ranked lists with score, reference ID, citation stratum, and binary relevance label.
- `results/sensitivity.csv`: BM25 citation-prior weight sensitivity analysis.
- `results/run_metadata.json`: data snapshot, settings, and script hashes for the reported execution.
- `results/recall_at_5.png` and `results/citation_sensitivity.png`: figures regenerated from the CSV outputs.

## Scope and limitations

Relevance labels are a small, manually specified set derived from the supplied review's own evidence map; they are not an independent benchmark. The corpus contains only the 15 works that review cites. One OpenAlex record lacks an abstract and is represented by its title. Citation counts are a single OpenAlex snapshot and are confounded by publication age, field, and database coverage. There are four queries, so results are descriptive and no significance tests are appropriate. The pilot supports a method demonstration and a defensible next experiment; it does not establish field-wide citation bias or language disparity.

## Data and citation

Bibliographic metadata and abstracts are obtained from OpenAlex, with the exact OpenAlex work IDs and DOI values stored in `data/reference_corpus.csv`. The source paper is identified in the manuscript and bibliography. The original review PDF is not redistributed in this project.
