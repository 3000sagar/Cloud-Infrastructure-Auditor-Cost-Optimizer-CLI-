"""Rich terminal report renderer."""

from typing import Iterable, Optional

from rich.console import Console
from rich.table import Table

from cloud_auditor.scanners.base import Finding

# Fixed width regardless of the detected terminal size, so AWS resource IDs
# (up to ~30 chars) stay intact under a narrow terminal or a test runner
# with a small default width.
TABLE_CONSOLE_WIDTH = 150


def build_findings_table(findings: Iterable[Finding]) -> Table:
    """Build a Rich table of findings. Resource IDs are no_wrap so a user
    can always copy the exact ID off the table to act on it."""
    findings = list(findings)
    table = Table(title=f"Audit findings ({len(findings)})")
    table.add_column("Resource ID", no_wrap=True)
    table.add_column("Type")
    table.add_column("Region")
    table.add_column("Issue")
    table.add_column("Recommendation")
    table.add_column("Est. $/mo", no_wrap=True)
    table.add_column("Risk", no_wrap=True)

    for finding in findings:
        savings = (
            f"${finding.estimated_monthly_savings:.2f}"
            if finding.estimated_monthly_savings is not None
            else "-"
        )
        table.add_row(
            finding.resource_id,
            finding.resource_type,
            finding.region,
            finding.issue,
            finding.recommendation,
            savings,
            finding.risk_level,
        )
    return table


def render_terminal_report(
    findings: Iterable[Finding], console: Optional[Console] = None
) -> None:
    """Print findings as a Rich table, or a clean message when there are none.

    Pass an explicit `console` (e.g. one bound to a StringIO) in tests to
    capture output without depending on a real terminal.
    """
    findings = list(findings)
    out = console or Console(width=TABLE_CONSOLE_WIDTH)

    if not findings:
        out.print("[green]No audit findings detected.[/green]")
        return

    out.print(build_findings_table(findings))