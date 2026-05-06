"""Render ReportSections to Markdown or HTML strings."""
from __future__ import annotations

from typing import List

from pipesight.reporter import ReportSection


def _md_table(section: ReportSection) -> str:
    sep = " | "
    header_line = sep.join(section.headers)
    divider = " | ".join(["---"] * len(section.headers))
    body_lines = [sep.join(row) for row in section.rows]
    return "\n".join([f"### {section.title}", header_line, divider, *body_lines])


def render_markdown(sections: List[ReportSection]) -> str:
    """Render all sections as a Markdown document."""
    parts = ["# PipeSight Report", ""]
    for section in sections:
        parts.append(_md_table(section))
        parts.append("")
    return "\n".join(parts)


def _html_table(section: ReportSection) -> str:
    th_cells = "".join(f"<th>{h}</th>" for h in section.headers)
    thead = f"<thead><tr>{th_cells}</tr></thead>"
    tbody_rows = ""
    for row in section.rows:
        td_cells = "".join(f"<td>{cell}</td>" for cell in row)
        tbody_rows += f"<tr>{td_cells}</tr>"
    tbody = f"<tbody>{tbody_rows}</tbody>"
    return (
        f"<section><h3>{section.title}</h3>"
        f"<table border='1' cellpadding='4' cellspacing='0'>{thead}{tbody}</table></section>"
    )


def render_html(sections: List[ReportSection]) -> str:
    """Render all sections as a self-contained HTML document."""
    body_parts = [_html_table(s) for s in sections]
    body = "\n".join(body_parts)
    return (
        "<!DOCTYPE html><html><head>"
        "<meta charset='utf-8'><title>PipeSight Report</title>"
        "<style>body{font-family:sans-serif;padding:1em}table{border-collapse:collapse}"
        "th{background:#333;color:#fff}td,th{padding:6px 10px}</style>"
        f"</head><body><h1>PipeSight Report</h1>\n{body}\n</body></html>"
    )
