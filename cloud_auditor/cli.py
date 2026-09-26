"""cloud-auditor command-line interface."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cloud_auditor import __version__
from cloud_auditor.scanners.aggregator import run_all_scanners
from cloud_auditor.auth.aws import AuthError, create_session, verify_credentials
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
        None, "--endpoint-url", help="Custom endpoint, e.g. http://127.0.0.1:5000 for moto."
    ),
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version."
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
    console.print(f"[yellow]{feature} is not implemented yet (planned for Week {week}).[/yellow]")
    raise typer.Exit(code=1)



@app.command()
def audit(ctx: typer.Context) -> None:
    """Scan for idle EC2, unattached EBS and unassociated Elastic IPs."""
    session = _authenticated_session(ctx)
    region = session.region_name

    findings = run_all_scanners(session, region, ctx.obj["endpoint_url"])

    if not findings:
        console.print("[green]No issues found.[/green]")
        raise typer.Exit(code=0)

    table = Table(title=f"Audit findings ({len(findings)})")
    table.add_column("Type")
    # AWS resource IDs run up to ~30 chars (eipalloc-xxxxxxxxxxxxxxxxx is the
    # longest). no_wrap here + a wide enough Console below means an ID is
    # never split across lines or truncated with an ellipsis -- a user has
    # to be able to copy the exact ID off this table to act on it.
    table.add_column("Resource", no_wrap=True)
    table.add_column("Issue")
    table.add_column("Recommendation")
    for finding in findings:
        table.add_row(
            finding.resource_type,
            finding.resource_id,
            finding.issue,
            finding.recommendation,
        )
    # Fixed width regardless of the detected terminal size, specifically so
    # resource IDs stay intact even when run under a narrow terminal or a
    # test runner that reports a small default width.
    Console(width=120).print(table)


@app.command()
def report(ctx: typer.Context) -> None:
    """Export audit results as JSON/CSV."""
    _not_implemented("report", 3)


@app.command()
def cleanup(ctx: typer.Context) -> None:
    """Dry-run or execute cleanup of flagged resources."""
    _not_implemented("cleanup", 3)


if __name__ == "__main__":
    app()