# Baseline validation report

## Status

**Pilot baselines validated for the stated fixed-corpus task. This is not a reproduction of an LLM paper-recommendation system.**

## VERIFIED checks

- The candidate corpus contains the 15 references listed in the supplied review, with distinct IDs R01-R15.
- DOI lookups use exact DOI endpoints; title-only lookups require a normalized exact title match.
- OpenAlex metadata response, timestamp, DOI, work ID, title, publication year, language, cited-by count, and abstract availability are saved in `data/`.
- The run checks reference uniqueness, query-gold membership, non-empty corpus, abstract-missing markers, expected relevance IDs, and consistent top-k evaluation.
- The sensitivity run asserts that lambda=0 exactly reproduces the BM25 ranking, lambda=1 reproduces the citation-only ranking, each ranking contains all 15 records exactly once, and bounded metrics remain within [0, 1].
- BM25, TF-IDF, and the citation-prior variant are deterministic; no random seed is required.
- The primary comparison preserves the BM25 lexical score and changes only its combination with the min-max normalized log citation count. Weight sensitivity is separately reported.
- Predictions/rankings and metrics are saved per query, so aggregate values can be recomputed from traceable rows.
- The frozen run completed on 2026-11-17 using 15 records and four queries. It is deterministic, CPU-only, and has no stochastic training stage.
- `scripts/check_environment.py` verifies the Python/dependency imports and that the topical match ranks first under both BM25 and TF-IDF; its actual output is saved in `results/environment_check.json`.

## Actual pilot results

| Method | Macro Recall@5 | Macro Precision@5 | Macro nDCG@5 | Low-citation Recall@5 | Mean log1p citations in top 5 |
|---|---:|---:|---:|---:|---:|
| BM25 | 0.9167 | 0.7000 | 0.9332 | 1.0000 | 3.6505 |
| TF-IDF | 0.9167 | 0.7000 | 0.9222 | 1.0000 | 3.5731 |
| BM25 + citation prior, lambda=0.25 | 0.8042 | 0.6000 | 0.8665 | 0.7500 | 5.6395 |

The pre-run decision rule is met in this run: the hybrid raises top-five citation exposure and lowers low-citation recall relative to both lexical baselines. This result is descriptive for the fixed 15-work bibliography and four review-derived queries. At lambda=0.10, low-citation Recall@5 remains 1.00; at 0.25 and 0.50 it is 0.75; at lambda=1.0 it is 0.00. R12 is displaced in Q2 and R04 is displaced in Q3 at lambda=0.25; R04 is also the title-only record.

## UNCERTAIN / scope constraints

- The review's cited works are not an independent or complete ground-truth retrieval benchmark.
- Relevance annotations are a single annotator's interpretation of the supplied review; no second reviewer or adjudication is available.
- OpenAlex citation counts are dynamic and are not normalized for age, field, or database coverage.
- R04 lacks an abstract in the frozen OpenAlex response and therefore contributes title-only text.
- Four queries and 15 candidates support descriptive comparison only. There is no valid basis for inferential significance claims.

## NEEDS CORRECTION before a stronger claim

- Do not call the output “overall recall,” “LLM recall,” or evidence of field-wide citation bias.
- Do not interpret low-citation stratum as a demographic or language fairness measure.
- For a general benchmark, add candidate records from a preregistered external search, independent relevance labels, complete abstract coverage, and age/field-aware citation controls.

## Reproduction

Use the included frozen corpus and run `python scripts/run_experiment.py`. The script version and data hashes are recorded in `results/run_metadata.json`.
