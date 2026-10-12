"""cloud-auditor command-line interface."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cloud_auditor import __version__
from cloud_auditor.audit.orchestrator import run_audit
from cloud_auditor.auth.aws import AuthError, create_session, verify_credentials
from cloud_auditor.cleanup.audit_log import write_cleanup_audit_log
from cloud_auditor.cleanup.executor import execute_cleanup, plan_cleanup
from cloud_auditor.reporting.csv_report import write_csv_report
from cloud_auditor.reporting.json_report import write_json_report
from cloud_auditor.reporting.rich_report import build_findings_table, render_terminal_report
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
def cleanup(
    ctx: typer.Context,
    execute: bool = typer.Option(
        False,
        "--execute",
        help=(
            "Actually delete the listed resources after an explicit "
            "y/N confirmation. Without this flag, cleanup always runs "
            "as a dry run and deletes nothing."
        ),
    ),
) -> None:
    """Dry-run (default) or execute cleanup of unattached EBS volumes
    and unassociated Elastic IPs.

    EC2 instances are never touched by this command, regardless of flags.
    """
    findings, _scan_regions = _collect_findings(ctx)
    cleanable = plan_cleanup(findings)
    skipped_count = len(findings) - len(cleanable)

    if not cleanable:
        console.print(
            "[green]Nothing eligible for cleanup -- no unattached EBS "
            "volumes or unassociated Elastic IPs found.[/green]"
        )
        if skipped_count:
            console.print(
                f"[dim]{skipped_count} other finding(s) (e.g. EC2 "
                "instances) are not eligible for automated cleanup and "
                "were left untouched.[/dim]"
            )
        return

    console.print(build_findings_table(cleanable))
    if skipped_count:
        console.print(
            f"[dim]{skipped_count} other finding(s) (e.g. EC2 instances) "
            "are not eligible for automated cleanup and were left "
            "untouched.[/dim]"
        )
    console.print(
        f"[yellow]DRY RUN: {len(cleanable)} resource(s) listed above "
        "would be deleted. Nothing has been deleted.[/yellow]"
    )

    if not execute:
        console.print(
            "[dim]Pass --execute to actually delete these resources "
            "(you will be asked to confirm).[/dim]"
        )
        return

    console.print(
        f"[bold red]About to permanently delete {len(cleanable)} "
        "resource(s) listed above.[/bold red]"
    )
    if not typer.confirm("Type y to confirm deletion, anything else to abort"):
        console.print("[yellow]Aborted. Nothing was deleted.[/yellow]")
        raise typer.Exit(code=1)

    session = _authenticated_session(ctx)
    results = execute_cleanup(session, cleanable, ctx.obj["endpoint_url"])

    deleted = [r for r in results if r.status == "deleted"]
    errors = [r for r in results if r.status == "error"]
    for result in deleted:
        console.print(f"  [green]Deleted[/green] {result.resource_type} {result.resource_id}")
    for result in errors:
        console.print(f"  [red]Error[/red] {result.resource_type} {result.resource_id}: {result.error}")

    console.print(f"[bold]{len(deleted)} deleted, {len(errors)} error(s).[/bold]")

    log_path = write_cleanup_audit_log(results)
    console.print(f"[dim]Logged to {log_path}[/dim]")

    if errors:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()