# Gate G1 research brief

## Review topic and key papers

AI-assisted literature curation, with emphasis on citation-status and language-related recall loss. The supplied review identifies both as separate mechanisms and cautions that benchmark results should be stratified. Original-source checks completed for Algaba et al. (ACL Anthology, 2025, DOI 10.18653/v1/2025.findings-naacl.381), Ikeguchi et al. (IOS Press, 2026, DOI 10.3233/SHTI260813), Tian et al. (arXiv:2501.00367, submitted 31 Dec 2024), and Agarwal et al. (TMLR/OpenReview, 2025).

## Research gap

The review calls for citation-stratified evaluation but supplies no runnable ranking benchmark. The pilot operationalizes one narrow part of that gap: what happens to retrieval of review-cited low-visibility sources when an explicit citation-count prior is added to a lexical ranker? This is a study of a ranking component, not an LLM recommender.

## Research question

For four topic queries derived from the review, how does adding an OpenAlex citation-count prior to BM25 affect Recall@5 for query-relevant references in the review's 15-work bibliography, especially those in the bottom citation-count third of that corpus?

## Pathway

Controlled comparative study with a targeted ranking modification. Baselines: BM25 and TF-IDF. Modified ranker: BM25 plus min-max normalized log1p citation count with a frozen primary weight of 0.25.

## Dataset and evaluation

The candidate corpus is the 15 numbered works cited by the supplied review. Metadata and abstracts were fetched from OpenAlex; the frozen snapshot and API work IDs are included. Query relevance labels come from the review's named sections and Table 2. The primary metric is macro Recall@5 over four queries. Deeper analysis: low-citation Recall@5 and citation-weight sensitivity. The low-citation stratum is the five lowest citation-count records in this corpus.

## Baselines, controls, and risks

All rankers use the same fixed candidate set, reconstructed title/abstract text, queries, labels, and K=5. The only primary modification is adding the citation prior to BM25. The corpus is small, labels are review-derived, one abstract is missing, citations are age- and field-confounded, and the benchmark cannot measure recall of uncited/unretrieved literature. Four queries do not support significance testing.

## Compute and first executable milestone

Local CPU, Python 3.12.10, no GPU, no training, deterministic ranking. Completed milestone: validated the 15 OpenAlex records, ran the environment-independent rankers, and saved query rankings, metrics, sensitivity analysis, and figures. The data snapshot is dated 2026-11-17.
