#!/usr/bin/env python3
"""Build synchronized LaTeX source and a reading PDF from manuscript.json."""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper"
RESULTS_DIR = ROOT / "results"
CONTENT_PATH = PAPER_DIR / "manuscript.json"
PROJECT_PDF = PAPER_DIR / "pilot_study.pdf"
OUTPUT_PDF = ROOT.parent / "output" / "pdf" / "Recall_Bias_Citation_Ranking_Pilot.pdf"

REF_KEYS = {
    1: "mahali2026review",
    2: "merton1968",
    3: "algaba2025citation",
    4: "tian2024recommendation",
    5: "agarwal2025litllms",
    6: "lewis2020rag",
    7: "ikeguchi2026language",
    8: "rasmussen2018nonenglish",
    9: "ridley2023linguistic",
    10: "matsui2024screening",
    11: "openalex2026",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def load_data() -> tuple[dict, dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    summary = {row["method"]: row for row in read_csv(RESULTS_DIR / "metrics_summary.csv")}
    queries = read_csv(RESULTS_DIR / "query_metrics.csv")
    sensitivity = read_csv(RESULTS_DIR / "sensitivity_summary.csv")
    return content, summary, {"query_metrics": queries, "sensitivity": sensitivity}


def number(value: str, places: int = 3) -> str:
    return f"{float(value):.{places}f}"


def reportlab_tables(summary: dict[str, dict[str, str]], details: dict[str, list[dict[str, str]]], content: dict) -> dict[str, tuple[list[str], list[list[str]]]]:
    bm25 = summary["BM25"]
    tfidf = summary["TF-IDF"]
    hybrid = summary["BM25+Citation (lambda=0.25)"]
    methods = ["BM25", "TF-IDF", "BM25+Citation (lambda=0.25)"]
    by_query_method = {(row["query_id"], row["method"]): row for row in details["query_metrics"]}

    query_annotations = []
    for q in content["query_names"]:
        config_query = next(item for item in json.loads((ROOT / "configs" / "experiment.json").read_text(encoding="utf-8"))["queries"] if item["query_id"] == q)
        query_annotations.append([
            content["query_names"][q],
            {
                "Q1_citation_recommendation": "Citation status in paper recommendations",
                "Q2_language_bias": "Language bias in reviews",
                "Q3_llm_screening": "LLM eligibility screening",
                "Q4_retrieval_rag": "Retrieval and RAG",
            }[q],
            ", ".join(config_query["gold_ref_ids"]),
            str(len(config_query["gold_ref_ids"])),
        ])

    summary_rows = []
    for method in methods:
        row = summary[method]
        label = "BM25 + citation prior (lambda=0.25)" if method.startswith("BM25+Citation") else method
        summary_rows.append([
            label,
            number(row["macro_recall_at_5"]),
            number(row["macro_precision_at_5"]),
            number(row["macro_ndcg_at_5"]),
            number(row["macro_low_citation_recall_at_5"]),
            number(row["macro_mean_log_citations_top_5"]),
        ])

    query_recall = []
    for q, qname in content["query_names"].items():
        query_recall.append([
            qname,
            number(by_query_method[(q, "BM25")]["recall_at_5"]),
            number(by_query_method[(q, "TF-IDF")]["recall_at_5"]),
            number(by_query_method[(q, "BM25+Citation (lambda=0.25)")]["recall_at_5"]),
        ])

    sensitivity_rows = []
    for row in details["sensitivity"]:
        sensitivity_rows.append([
            number(row["lambda"], 2),
            number(row["macro_recall_at_5"]),
            number(row["macro_low_citation_recall_at_5"]),
            number(row["mean_log_citations_top_5"]),
        ])

    return {
        "query_annotations": (["Query", "Topic", "Relevant reference IDs", "n"], query_annotations),
        "primary_summary": (["Method", "Recall@5", "Precision@5", "nDCG@5", "Low-citation R@5", "Mean log1p cites, top 5"], summary_rows),
        "query_recall": (["Query", "BM25", "TF-IDF", "BM25 + citation prior"], query_recall),
        "sensitivity": (["lambda", "Macro Recall@5", "Low-citation Recall@5", "Mean log1p cites, top 5"], sensitivity_rows),
    }


def replace_metrics(text: str, summary: dict[str, dict[str, str]]) -> str:
    bm25 = summary["BM25"]
    tfidf = summary["TF-IDF"]
    hybrid = summary["BM25+Citation (lambda=0.25)"]
    values = {
        "{{BM25_R5}}": number(bm25["macro_recall_at_5"]),
        "{{TFIDF_R5}}": number(tfidf["macro_recall_at_5"]),
        "{{HYBRID_R5}}": number(hybrid["macro_recall_at_5"]),
        "{{BM25_LOW}}": number(bm25["macro_low_citation_recall_at_5"]),
        "{{TFIDF_LOW}}": number(tfidf["macro_low_citation_recall_at_5"]),
        "{{HYBRID_LOW}}": number(hybrid["macro_low_citation_recall_at_5"]),
        "{{BM25_CITES}}": number(bm25["macro_mean_log_citations_top_5"]),
        "{{TFIDF_CITES}}": number(tfidf["macro_mean_log_citations_top_5"]),
        "{{HYBRID_CITES}}": number(hybrid["macro_mean_log_citations_top_5"]),
    }
    for token, value in values.items():
        text = text.replace(token, value)
    return text


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_text(text: str) -> str:
    parts = re.split(r"(\[(?:\d+(?:,\s*\d+)*)\])", text)
    result = []
    for part in parts:
        match = re.fullmatch(r"\[((?:\d+)(?:,\s*\d+)*)\]", part)
        if match:
            nums = [int(number.strip()) for number in match.group(1).split(",")]
            result.append(r"\cite{" + ",".join(REF_KEYS[num] for num in nums) + "}")
        else:
            result.append(latex_escape(part))
    return "".join(result)


def tex_table(headers: list[str], rows: list[list[str]], caption: str) -> str:
    columns = "".join("X" for _ in headers)
    caption = re.sub(r"^(?:Table|Figure)\s+\d+\.\s*", "", caption)
    lines = [
        r"\begin{table}[H]",
        r"\caption{" + latex_text(caption) + "}",
        r"\centering\small",
        r"\begin{tabularx}{\linewidth}{" + columns + "}",
        r"\toprule",
        " & ".join(latex_text(item) for item in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(latex_text(item) for item in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabularx}", r"\end{table}"])
    return "\n".join(lines)


def generate_tex(content: dict, summary: dict, tables: dict) -> str:
    lines = [
        r"\documentclass[acmsmall,nonacm]{acmart}",
        r"\settopmatter{printacmref=false}",
        r"\citestyle{acmnumeric}",
        r"\usepackage{booktabs}",
        r"\usepackage{tabularx}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\title{" + latex_escape(content["title"]) + "}",
        r"\author{" + latex_escape(content["author"]) + "}",
        r"\affiliation{\institution{" + latex_escape(content["affiliation"]) + r"}\city{" + latex_escape(content["city"]) + r"}\country{" + latex_escape(content["country"]) + "}}",
        r"\begin{document}",
        r"\begin{abstract}" + latex_text(replace_metrics(content["abstract"], summary)) + r"\end{abstract}",
        r"\keywords{" + latex_escape(", ".join(content["keywords"])) + "}",
        r"\maketitle",
    ]
    for section in content["sections"]:
        lines.append(r"\section*{" + latex_escape(section["heading"]) + "}")
        for item in section["items"]:
            if item["type"] == "p":
                lines.append(latex_text(replace_metrics(item["text"], summary)) + r"\par")
            elif item["type"] == "table":
                headers, rows = tables[item["source"]]
                lines.append(tex_table(headers, rows, item["title"]))
            elif item["type"] == "figure":
                caption = re.sub(r"^(?:Table|Figure)\s+\d+\.\s*", "", item["caption"])
                lines.extend([
                    r"\begin{figure}[H]",
                    r"\centering\includegraphics[width=.92\linewidth]{figures/" + item["file"] + "}",
                    r"\caption{" + latex_text(caption) + "}",
                    r"\end{figure}",
                ])
            else:
                raise ValueError(f"Unknown manuscript item type {item['type']}")
    lines.extend([r"\bibliographystyle{ACM-Reference-Format}", r"\bibliography{references}", r"\end{document}"])
    return "\n\n".join(lines) + "\n"


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("PaperTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19, leading=22, alignment=TA_CENTER, textColor=colors.HexColor("#15324B"), spaceAfter=8),
        "author": ParagraphStyle("PaperAuthor", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, alignment=TA_CENTER, spaceAfter=3),
        "affiliation": ParagraphStyle("Affiliation", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#475569"), spaceAfter=12),
        "abstract_label": ParagraphStyle("AbstractLabel", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.HexColor("#15324B"), spaceAfter=3),
        "abstract": ParagraphStyle("Abstract", parent=base["BodyText"], fontName="Helvetica", fontSize=8.8, leading=12, alignment=TA_JUSTIFY, backColor=colors.HexColor("#F2F6F9"), borderPadding=8, spaceAfter=7),
        "keywords": ParagraphStyle("Keywords", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, spaceAfter=9),
        "h1": ParagraphStyle("SectionHeading", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=15, textColor=colors.HexColor("#15324B"), spaceBefore=9, spaceAfter=5, keepWithNext=True),
        "body": ParagraphStyle("PaperBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.1, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=6, splitLongWords=0),
        "caption": ParagraphStyle("TableCaption", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10, alignment=TA_LEFT, spaceBefore=4, spaceAfter=4),
        "table": ParagraphStyle("TableCell", parent=base["Normal"], fontName="Helvetica", fontSize=7.6, leading=9.3, alignment=TA_LEFT),
        "table_head": ParagraphStyle("TableHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.white),
        "reference": ParagraphStyle("Reference", parent=base["Normal"], fontName="Helvetica", fontSize=7.9, leading=10, leftIndent=13, firstLineIndent=-13, spaceAfter=5),
    }


def make_reportlab_table(headers: list[str], rows: list[list[str]], available_width: float, styles: dict) -> Table:
    if len(headers) == 6:
        ratios = [1.9, 0.75, 0.83, 0.70, 1.10, 1.63]
    elif len(headers) == 4 and headers[0] == "Query":
        ratios = [1.75, 0.68, 0.68, 1.0]
    elif len(headers) == 4 and headers[0] == "lambda":
        ratios = [0.65, 1.0, 1.42, 1.55]
    elif len(headers) == 4:
        ratios = [0.7, 1.7, 1.4, 0.35]
    else:
        ratios = [1] * len(headers)
    total = sum(ratios)
    widths = [available_width * ratio / total for ratio in ratios]
    data = [[Paragraph(escape_cell(cell), styles["table_head"]) for cell in headers]]
    for row in rows:
        data.append([Paragraph(escape_cell(cell), styles["table"]) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15324B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def escape_cell(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D5DEE7"))
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, 0.53 * inch, width - doc.rightMargin, 0.53 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(doc.leftMargin, 0.36 * inch, "Citation-prior retrieval pilot | 17 November 2026")
    canvas.drawRightString(width - doc.rightMargin, 0.36 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(content: dict, summary: dict, detail: dict, tables: dict) -> None:
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PROJECT_PDF), pagesize=A4,
        rightMargin=0.68 * inch, leftMargin=0.68 * inch,
        topMargin=0.62 * inch, bottomMargin=0.68 * inch,
        title=content["title"], author=content["author"],
    )
    story = [
        Paragraph(escape_cell(content["title"]), styles["title"]),
        Paragraph(escape_cell(content["author"]), styles["author"]),
        Paragraph(escape_cell(f"{content['affiliation']}, {content['city']}, {content['country']}"), styles["affiliation"]),
        Paragraph("Abstract", styles["abstract_label"]),
        Paragraph(escape_cell(replace_metrics(content["abstract"], summary)), styles["abstract"]),
        Paragraph("<b>Keywords:</b> " + escape_cell("; ".join(content["keywords"])), styles["keywords"]),
    ]
    available_width = A4[0] - doc.leftMargin - doc.rightMargin
    for section in content["sections"]:
        story.append(Paragraph(escape_cell(section["heading"]), styles["h1"]))
        for item in section["items"]:
            if item["type"] == "p":
                story.append(Paragraph(escape_cell(replace_metrics(item["text"], summary)), styles["body"]))
            elif item["type"] == "table":
                headers, rows = tables[item["source"]]
                story.append(KeepTogether([
                    Paragraph(escape_cell(item["title"]), styles["caption"]),
                    make_reportlab_table(headers, rows, available_width, styles),
                ]))
                story.append(Spacer(1, 5))
            elif item["type"] == "figure":
                image_path = PAPER_DIR / "figures" / item["file"]
                original = Image(str(image_path))
                draw_width = min(available_width, 470)
                draw_height = original.imageHeight * draw_width / original.imageWidth
                img = Image(str(image_path), width=draw_width, height=draw_height)
                story.append(KeepTogether([img, Paragraph(escape_cell(item["caption"]), styles["caption"])]))
            else:
                raise ValueError(f"Unknown manuscript item type {item['type']}")
    if content["references"]:
        first_reference = Paragraph(f"[1] {escape_cell(content['references'][0])}", styles["reference"])
        story.append(KeepTogether([Paragraph("References", styles["h1"]), first_reference]))
    for i, reference in enumerate(content["references"][1:], 2):
        story.append(Paragraph(f"[{i}] {escape_cell(reference)}", styles["reference"]))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_PDF, OUTPUT_PDF)


def main() -> None:
    content, summary, details = load_data()
    tables = reportlab_tables(summary, details, content)
    (PAPER_DIR / "main.tex").write_text(generate_tex(content, summary, tables), encoding="utf-8")
    build_pdf(content, summary, details, tables)
    print(f"Wrote synchronized LaTeX source: {PAPER_DIR / 'main.tex'}")
    print(f"Wrote reading PDF: {PROJECT_PDF}")
    print(f"Copied final PDF: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
