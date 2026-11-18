# Internal technical review and revision record

This is an AI-assisted internal audit of the current pilot draft, not an independent peer review. Concerns are limited to claims and evidence visible in the included files.

| Priority | Concern | Why it matters | Revision or required next step | Status |
|---|---|---|---|---|
| Major | The candidate set is the source review's own 15 references and the query labels are derived from that review. | This can overstate relevance and cannot reveal relevant works absent from the bibliography. | The manuscript calls the task a review-grounded pilot, defines positives narrowly, and disclaims field-wide/end-to-end recall. A stronger study needs an independently searched corpus and double-screened labels. | Addressed in manuscript; external benchmark remains future work. |
| Major | Citation counts are record-version-specific, age-confounded, and not field-normalized. | A rank change can result from index/version choice or publication age as well as visibility. | The frozen DOI record and OpenAlex IDs are retained; R06 duplicate-version discrepancy and R01 publication-year difference are disclosed. Future work should use matched/year-normalized counts and audit multiple records. | Addressed as a limitation. |
| Major | The pilot does not test an LLM recommender or language disparity. | The supplied review covers both, but this experiment only changes a lexical ranker. | The research question and conclusions are restricted to a citation prior over the fixed bibliography; the language evidence is treated as motivation only. | Addressed in manuscript. |
| Major | R04 has title-only text and is a low-citation positive for Q3. | Its miss may reflect missing abstract content as well as the citation feature. | The missing abstract is recorded, the R04 displacement is isolated as an error case, and causal attribution is qualified. | Addressed in manuscript and data README. |
| Minor | Four manually constructed queries are insufficient for statistical inference. | Query-level variation is high and queries are not an independent random sample. | Report descriptive metrics only; do not calculate significance tests. | Addressed. |
| Minor | The source review is narrative and may contain evidence/selection limitations. | The bibliography is not a complete benchmark or an independently validated systematic-review sample. | Carry this limitation into the scope statement and recommend independent search and screening for follow-up. | Addressed. |

## Figure and result audit

- Primary macro values in Table 2 are read from `results/metrics_summary.csv` by the manuscript builder.
- Query-level Recall@5 in Table 3 is read from `results/query_metrics.csv`.
- Weight sensitivity in Table 4 and Figure 2 is read from `results/sensitivity_summary.csv`.
- The manuscript builder uses the same `paper/manuscript.json` content for the PDF and LaTeX source. No result numbers are hand-entered into tables.
- The PDF was rendered and visually inspected after generation. The table captions remain with their tables, the two figures are legible, and no text or data markers are clipped.
