# AI assistance and research provenance log

This log records work actually performed in this session. It does not claim that a student independently authored or verified steps not recorded here.

| Task | AI-assisted action | Human/source evidence used | Verification and outcome |
|---|---|---|---|
| Extract assignment requirements | Parsed the supplied prompts PDF and summarized its evidence, comparison, reproducibility, and integrity requirements. | `prompts.pdf`, pages 1-11. | Checked extracted text and rendered page contact sheet. |
| Map review to an experiment | Proposed a fixed-bibliography ranking pilot around citation-status bias. | Supplied review, especially Sections 2-3, 7-9, Table 2, and references. | Narrowed claims because the review provides no code, dataset, logs, or experimental outputs. |
| Resolve bibliographic metadata | Queried OpenAlex using the listed DOIs or exact titles and retrieved title, year, citation count, language, work ID, and abstract metadata. | OpenAlex public API. | All 15 records resolved; saved IDs and metadata. One record lacked an abstract. |
| Verify central original sources | Checked primary publisher/repository pages for citation-bias, language-bias, and recommendation sources. | ACL Anthology [2], IOS Press [5], arXiv [15], TMLR/OpenReview [1]. | Confirmed identity and key background claims from source pages; recorded the evidence links and the arXiv submission date for [15]. |
| Correct bibliographic metadata | Compared Crossref's record for Algaba et al. with the ACL Anthology landing page. | Crossref returned pages 6829-6864, while the official ACL Anthology page lists 6844-6879. | Used the official venue page's volume and page metadata in the manuscript/BibTeX; recorded this provider disagreement in `sources_checked.md`. |
| Generate implementation | Wrote deterministic BM25, TF-IDF, citation-prior, metric, and plotting code. | Frozen protocol and stored corpus snapshot. | Ran the script and retained output CSVs, run metadata, and figures. |
| Debug document generation | First report build failed because the figure's visual draw size had not updated ReportLab's layout size. | Actual `LayoutError` from the build command and the rendered image dimensions. | Passed width and height to the Image flowable constructor; the next build completed and the pages were visually inspected. |
| Debug ACM source | The first Tectonic compile rejected the author affiliation because `acmart` requires a country and recommends a city. | Actual compiler error: `No country present for an affiliation.` | Added explicit city and country fields to the shared manuscript data and regenerated the ACM source. The retry exited successfully; the ACM layout still emits box/font warnings, so the visually reviewed ReportLab reading PDF is the handoff PDF. |
| Handle uncertainty | Kept the corpus review-limited and described relevance labels as review-derived. | Only the supplied review and its references were provided. | Reported missing abstracts, dynamic citation data, small query count, absent independent labels, and unknown out-of-bibliography recall. |

## Limitations and human decisions

- The AI selected a feasible pilot rather than claiming the full multi-gate course assignment had been completed; no student prompt history, commits, or independent review were supplied.
- The relevance sets are transparent, review-derived annotations, not author-independent labels.
- The AI cannot verify that the student personally reviewed the original publications or understands the code. The student must read and defend the protocol, code, and limitations before submission.
- No LLM recommendation output, benchmark, or student execution log was provided; none is claimed here.
