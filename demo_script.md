# Five-minute demonstration outline

1. **Question and source (45 sec):** Show `research_brief.md` and the original review passages in Sections 3, 7, and 9. Explain the limited question about a citation prior and top-k recall.
2. **Data and labels (60 sec):** Open `data/reference_corpus.csv`, `configs/experiment.json`, and `data/gold_labels.csv`. Point out the 15-work corpus, query-specific labels, OpenAlex snapshot date, and R04 missing abstract.
3. **Baseline and modification (75 sec):** Walk through `scripts/run_experiment.py`: BM25, TF-IDF, min-max normalized log citation count, and lambda=0.25. Explain the single controlled change.
4. **Re-run (60 sec):** From the project folder, run `python scripts/run_experiment.py`. Open `results/metrics_summary.csv` and `results/rankings.csv` to trace a macro number back to each query and ranked reference.
5. **Findings and limits (60 sec):** Show `results/recall_at_5.png` and `results/citation_sensitivity.png`. Report that the hybrid increased mean log citation exposure while reducing low-citation recall on this fixed corpus. State that labels are review-derived, there are four queries, the source corpus is incomplete by design, and the experiment does not evaluate an LLM or language parity.
