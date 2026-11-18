# Manuscript build notes

`paper/manuscript.json` is the shared manuscript content source. `scripts/build_manuscript.py` reads that file and the actual metric CSVs, then writes:

- `paper/main.tex`, an ACM `acmart` source using the included `references.bib` and local figure files;
- `paper/pilot_study.pdf`, a reading PDF with tables and figures populated from the saved results;
- `output/pdf/Recall_Bias_Citation_Ranking_Pilot.pdf`, the standalone final copy.

The PDF reading copy is generated with ReportLab. The LaTeX source uses the ACM `acmart` class and was compiled successfully with Tectonic 0.17. The local ACM compile still emits font and box-layout warnings; use `paper/pilot_study.pdf` as the visually reviewed handoff copy, and check the layout again if compiling the source in Overleaf. The result tables and manuscript text are synchronized through the builder. Rebuild after changing queries, code, or data so the paper does not retain stale results.
