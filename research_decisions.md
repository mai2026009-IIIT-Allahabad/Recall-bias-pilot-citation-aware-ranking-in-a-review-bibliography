# Research decisions and evidence ledger

## Scope from the supplied review

- **VERIFIED:** The source is a narrative review, not a registered systematic review. It defines recall as TP/(TP+FN) and subgroup recall difference in Section 2.
- **VERIFIED:** The review identifies citation-status and language/corpus coverage as two recall-bias axes, then proposes language- and citation-stratified benchmarks, provenance evaluation, corpus audits, adaptive retrieval, and human calibration (Sections 3, 8, and 9).
- **VERIFIED:** Section 7, Table 2, explicitly cautions that the listed studies are not a leaderboard because tasks, domains, and protocols differ.
- **VERIFIED:** The review's reference list contains 15 works used to build this pilot's candidate corpus. OpenAlex returned records for all 15 title/DOI lookups; one record (R04) had no abstract in the returned metadata.
- **VERIFIED:** The ACL Anthology record for Algaba et al. [2] confirms the title, authors, year, DOI, pages, and the reported high-citation bias finding.
- **VERIFIED:** The IOS Press record for Ikeguchi et al. [5] confirms the title, authors, DOI, sample sizes (2,911 English and 483 non-English abstracts), and the reported sensitivity ranges for translated and direct multilingual screening.
- **VERIFIED:** The arXiv record for Tian et al. [15] identifies the title/authors and says it was submitted on 31 Dec 2024; its described recommendation experiment reports citation-count preference. The source review's year 2024 is consistent with that submission date.
- **VERIFIED:** The TMLR/OpenReview record for Agarwal et al. [1] confirms the paper identity and describes retrieval/reranking evaluation; a code link is present on the primary paper page.

## Gap and candidate study

- **INFERRED:** A small controlled ranking study can operationalize the review's citation-status concern by holding the candidate bibliography and four query-specific relevance sets fixed, then adding an explicit citation-count prior to a lexical ranker.
- **UNKNOWN:** Whether the same effect occurs in a production literature search system, in a broader AI corpus, or in an LLM recommendation system. This pilot does not test those systems.
- **UNKNOWN:** Recall over relevant works that are not cited in the source review. The fixed bibliography cannot estimate this.

## Frozen question and pathway

**Question:** For four review-grounded topic queries over the review's 15 cited works, how does adding an OpenAlex citation-count prior to BM25 affect Recall@5 for manually annotated relevant references, especially the lowest-citation third of the corpus?

**Pathway:** Controlled comparative study with a targeted ranking modification. Compare BM25 and TF-IDF to BM25 plus a normalized log citation-count prior (primary weight 0.25); run a predeclared lambda sensitivity analysis.

### Alternatives considered

| Pathway | Candidate | Feasibility and reason |
|---|---|---|
| Reproduction plus extension | Reproduce LitLLMs retrieval/reranking, then test a citation-stratified condition. | The primary page exposes a code link, but reproducing its full LLM pipeline needs its benchmark, model access, and protocol. Not attempted in this local pilot. |
| Controlled comparison | Compare BM25 and TF-IDF on common candidate records and fixed review-derived queries. | Feasible locally with public metadata and identical conditions; selected as the baseline comparison. |
| Targeted modification | Add citation count to BM25 while preserving the original lexical score. | One isolated, low-compute change that directly tests the review's citation-status concern; selected as the experimental modification. |

**Primary metric:** Macro Recall@5 over four queries. **Deeper analysis:** low-citation Recall@5 and citation-prior weight sensitivity. No significance tests: four non-independent, manually designed queries are not a statistical sample.

## Feasibility and first executable milestone

- **VERIFIED:** OpenAlex responded to DOI/title requests for the 15 references and supplied citation metadata and 14 abstracts as of the recorded snapshot; one record is title-only.
- **INFERRED:** The experiment is feasible on a local CPU because corpus size is 15 records and rankers are sparse lexical baselines.
- **UNKNOWN:** Institutionally required data/license language beyond OpenAlex's public API terms; check current terms before public redistribution.
- **VERIFIED:** A title search for R06 exposed two OpenAlex records with the same work title and substantially different counts. The experiment pins the arXiv DOI record and labels its cited-by value as record-specific; no deduplication claim is made.
- **Completed:** The frozen metadata CSV, query labels, ranking code, run outputs, and figures are included in this project.

## Decisions made before ranking outputs

1. Use only the 15 works in the review bibliography; do not use their rank as an estimate of field-wide recall.
2. Fix four queries and positive reference IDs using review sections/tables before ranking code runs.
3. Use BM25 and TF-IDF as lexical baselines; add citation count only to the BM25 score.
4. Normalize BM25 and log1p citation counts within the fixed 15-record corpus. Set primary lambda to 0.25 and sensitivity values to 0, 0.1, 0.25, 0.5, and 1.0.
5. Define the low-citation group as the lowest five works in this corpus, with ties broken by reference ID.
6. Report query-level outcomes, macro averages, and errors/limitations. Do not claim significance.

## Next actions for a stronger follow-up

1. Build an independently screened benchmark with candidate records discovered from a prespecified database query, including relevant non-cited works.
2. Normalize citation exposure by age/field or compare citation priors within matched publication-year strata.
3. Add a second reviewer and adjudication for relevance labels; evaluate multiple databases and include language strata.
