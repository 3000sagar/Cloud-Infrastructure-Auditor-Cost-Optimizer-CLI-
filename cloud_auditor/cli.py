"""cloud-auditor command-line interface."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cloud_auditor import __version__
from cloud_auditor.audit.orchestrator import run_audit
from cloud_auditor.auth.aws import AuthError, create_session, verify_credentials
from cloud_auditor.reporting.csv_report import write_csv_report
from cloud_auditor.reporting.json_report import write_json_report
from cloud_auditor.reporting.rich_report import render_terminal_report
from cloud_auditor.scanners.base import ScannerError
from cloud_auditor.utils.regions import RegionDiscoveryError, get_enabled_regions

app = typer.Typer(
    help="Cloud Infrastructure Auditor & Cost Optimizer",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"cloud-auditor {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name."),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Default region."),
    endpoint_url: Optional[str] = typer.Option(
        None,
        "--endpoint-url",
        help="Custom endpoint, e.g. http://127.0.0.1:5000 for moto.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version.",
    ),
) -> None:
    """Global options shared by every command."""
    ctx.obj = {"profile": profile, "region": region, "endpoint_url": endpoint_url}


def _authenticated_session(ctx: typer.Context):
    opts = ctx.obj
    try:
        session = create_session(opts["profile"], opts["region"], opts["endpoint_url"])
        verify_credentials(session, opts["endpoint_url"])
    except AuthError as exc:
        console.print(f"[red]Auth error:[/red] {exc}")
        raise typer.Exit(code=1)
    return session


@app.command()
def whoami(ctx: typer.Context) -> None:
    """Show which AWS identity the tool is authenticated as."""
    opts = ctx.obj
    try:
        session = create_session(opts["profile"], opts["region"], opts["endpoint_url"])
        identity = verify_credentials(session, opts["endpoint_url"])
    except AuthError as exc:
        console.print(f"[red]Auth error:[/red] {exc}")
        raise typer.Exit(code=1)

    console.print(f"Account: {identity['Account']}")
    console.print(f"ARN:     {identity['Arn']}")


@app.command()
def regions(ctx: typer.Context) -> None:
    """List the AWS regions enabled for this account."""
    session = _authenticated_session(ctx)

    try:
        names = get_enabled_regions(session, ctx.obj["endpoint_url"])
    except RegionDiscoveryError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    table = Table(title=f"Enabled regions ({len(names)})")
    table.add_column("Region")

    for name in names:
        table.add_row(name)

    console.print(table)


def _not_implemented(feature: str, week: int) -> None:
    console.print(
        f"[yellow]{feature} is not implemented yet "
        f"(planned for Week {week}).[/yellow]"
    )
    raise typer.Exit(code=1)


def _collect_findings(ctx: typer.Context):
    """Authenticate, choose the regions to scan, run the audit.

    An explicit --region scans only that region. Without it, every region
    enabled for the account is scanned. Returns (findings, regions).
    """
    session = _authenticated_session(ctx)
    opts = ctx.obj

    if opts["region"]:
        scan_regions = [opts["region"]]
    else:
        try:
            scan_regions = get_enabled_regions(session, opts["endpoint_url"])
        except RegionDiscoveryError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    console.print(f"[bold]Scanning {len(scan_regions)} AWS region(s)...[/bold]")

    try:
        findings = run_audit(
            session=session,
            regions=scan_regions,
            endpoint_url=opts["endpoint_url"],
        )
    except ScannerError as exc:
        console.print(f"[red]Scan error:[/red] {exc}")
        raise typer.Exit(code=1)

    return findings, scan_regions


@app.command()
def audit(ctx: typer.Context) -> None:
    """Scan for idle EC2, unattached EBS and unassociated Elastic IPs."""
    findings, _scan_regions = _collect_findings(ctx)
    render_terminal_report(findings)


SUPPORTED_FORMATS = ("json", "csv", "terminal")


@app.command()
def report(
    ctx: typer.Context,
    fmt: str = typer.Option(
        "json", "--format", "-f", help="Report format: json, csv, or terminal."
    ),
    output_dir: Path = typer.Option(
        Path("reports"),
        "--output-dir",
        help="Directory to write the report into (ignored for terminal).",
    ),
) -> None:
    """Run an audit and show or export the results."""
    if fmt not in SUPPORTED_FORMATS:
        console.print(
            f"[red]Unknown format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}.[/red]"
        )
        raise typer.Exit(code=2)

    findings, scan_regions = _collect_findings(ctx)

    if fmt == "terminal":
        render_terminal_report(findings)
        return
    if fmt == "csv":
        path = write_csv_report(findings, output_dir)
    else:
        path = write_json_report(findings, scan_regions, output_dir)
    console.print(f"Wrote {len(findings)} finding(s) to {path}")


@app.command()
def cleanup(ctx: typer.Context) -> None:
    """Dry-run or execute cleanup of flagged resources."""
    _not_implemented("cleanup", 3)


if __name__ == "__main__":
    app()