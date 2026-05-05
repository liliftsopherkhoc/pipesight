"""Render alert results to the terminal."""
from __future__ import annotations

from typing import List

from pipesight.alerter import Alert

_RED = "\033[31m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _severity_color(alert: Alert) -> str:
    return _RED if alert.is_critical else _YELLOW


def render_alerts(alerts: List[Alert], *, color: bool = True) -> str:
    """Return a human-readable string summarising *alerts*.

    Parameters
    ----------
    alerts:
        List produced by :func:`pipesight.alerter.check_alerts`.
    color:
        When *True* ANSI escape codes are included.

    Returns
    -------
    str
        Multi-line report, or a short "all clear" message when empty.
    """
    if not alerts:
        ok = f"{_BOLD}✓ No alerts fired — all steps within thresholds.{_RESET}"
        return ok if color else "✓ No alerts fired — all steps within thresholds."

    lines: List[str] = []
    header = f"{_BOLD}⚠  Pipeline Alerts ({len(alerts)} step(s)){_RESET}"
    lines.append(header if color else f"⚠  Pipeline Alerts ({len(alerts)} step(s))")
    lines.append("─" * 50)

    for alert in alerts:
        severity = "CRITICAL" if alert.is_critical else "WARNING"
        col = _severity_color(alert) if color else ""
        rst = _RESET if color else ""
        bold = _BOLD if color else ""
        lines.append(f"{col}{bold}[{severity}]{rst} {alert.step_name}")
        for v in alert.violations:
            lines.append(f"  • {v}")

    lines.append("─" * 50)
    return "\n".join(lines)
