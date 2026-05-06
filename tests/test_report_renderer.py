"""Unit tests focused on the low-level rendering helpers."""
from __future__ import annotations

from pipesight.reporter import ReportSection
from pipesight.report_renderer import render_markdown, render_html, _md_table, _html_table


def _section() -> ReportSection:
    return ReportSection(
        title="Test Section",
        headers=["Name", "Value"],
        rows=[["alpha", "1"], ["beta", "2"]],
    )


# ---------------------------------------------------------------------------
# _md_table
# ---------------------------------------------------------------------------

def test_md_table_contains_title():
    s = _section()
    out = _md_table(s)
    assert "### Test Section" in out


def test_md_table_contains_headers():
    s = _section()
    out = _md_table(s)
    assert "Name" in out
    assert "Value" in out


def test_md_table_contains_divider():
    s = _section()
    out = _md_table(s)
    assert "---" in out


def test_md_table_contains_rows():
    s = _section()
    out = _md_table(s)
    assert "alpha" in out
    assert "beta" in out


# ---------------------------------------------------------------------------
# _html_table
# ---------------------------------------------------------------------------

def test_html_table_contains_section_tag():
    s = _section()
    out = _html_table(s)
    assert "<section>" in out
    assert "</section>" in out


def test_html_table_contains_th_for_each_header():
    s = _section()
    out = _html_table(s)
    assert out.count("<th>") == len(s.headers)


def test_html_table_contains_td_for_each_cell():
    s = _section()
    out = _html_table(s)
    expected_cells = sum(len(row) for row in s.rows)
    assert out.count("<td>") == expected_cells


def test_html_table_h3_title():
    s = _section()
    out = _html_table(s)
    assert "<h3>Test Section</h3>" in out


# ---------------------------------------------------------------------------
# render_markdown / render_html full document
# ---------------------------------------------------------------------------

def test_render_markdown_multiple_sections():
    s1 = _section()
    s2 = ReportSection(title="Other", headers=["X"], rows=[["z"]])
    md = render_markdown([s1, s2])
    assert "### Test Section" in md
    assert "### Other" in md


def test_render_html_multiple_sections():
    s1 = _section()
    s2 = ReportSection(title="Other", headers=["X"], rows=[["z"]])
    html = render_html([s1, s2])
    assert "Test Section" in html
    assert "Other" in html


def test_render_html_charset_meta():
    html = render_html([_section()])
    assert "charset='utf-8'" in html
