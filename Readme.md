# Cloud Infrastructure Auditor & Cost Optimizer

> A Python CLI for auditing AWS infrastructure, identifying common sources of cloud waste, and exporting audit findings to JSON or CSV.

[![Tests](https://github.com/3000sagar/Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-/actions/workflows/tests.yml/badge.svg)](https://github.com/3000sagar/Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Boto3-orange?logo=amazon-aws)](https://aws.amazon.com/sdk-for-python/)
[![CLI](https://img.shields.io/badge/CLI-Typer-009688)](https://typer.tiangolo.com/)
[![Terminal](https://img.shields.io/badge/Terminal-Rich-purple)](https://rich.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Project Status

The current `main` branch contains a working AWS audit pipeline for:

- AWS credential verification and identity checks
- Enabled-region discovery
- Multi-region auditing
- Unattached EBS volume detection
- Unassociated Elastic IP detection
- EC2 CPU-utilization analysis using CloudWatch
- Estimated monthly savings per finding (EBS, Elastic IP, EC2)
- Risk-level labeling per finding
- JSON report export
- CSV report export
- Rich terminal report export (`report --format terminal`)
- Optimization score (0-100, based on finding risk levels)
- EBS/Elastic IP cleanup with dry-run and explicit confirmation (`cleanup` / `cleanup --execute`)
- Persisted cleanup audit log (`logs/cleanup-audit.jsonl`) for every confirmed deletion
- Retry/backoff configuration
- Automated tests using `pytest` and `moto`
- GitHub Actions CI, running the full test suite on every push/PR to `main` across Python 3.10, 3.11, and 3.12
- Standalone executable packaging via PyInstaller

The following parts are currently **not implemented**:

- EC2 cleanup (stop/resize) -- intentionally out of scope, see the Cleanup section
- PyPI/internal package distribution

**Scope:** AWS only. GCP and Azure are not implemented in this repository.

---

## Overview

**Cloud Infrastructure Auditor & Cost Optimizer** is a command-line tool for DevOps, Cloud Engineering, and FinOps workflows.

It connects to AWS through Boto3 and scans the selected region(s) for three currently supported finding types:

1. Unattached EBS volumes
2. Unassociated Elastic IP addresses
3. Running EC2 instances with average CPU utilization below a configurable threshold over a configurable time window

Each finding is enriched with an estimated monthly savings figure and a risk level before it reaches a report or the terminal table. Audit findings can be exported as JSON or CSV for further review.

The project is also designed to run locally with `moto`, allowing AWS API interactions to be tested without provisioning real AWS resources.

---

## Current Features

### AWS Authentication

The project uses Boto3's standard credential resolution mechanisms.

Supported approaches include:

- AWS environment variables
- AWS CLI profiles
- IAM roles and the normal AWS credential provider chain
- Local test credentials when a custom `--endpoint-url` is used and no credentials are available

Use `whoami` to verify the identity before auditing an account.

### Region Discovery

When no `--region` is supplied, the CLI discovers enabled AWS regions through EC2 `DescribeRegions` and audits every returned region.

When `--region` is supplied, only that region is scanned.

### EBS Scanner

The EBS scanner searches for volumes whose AWS status is `available`, which represents unattached EBS volumes.

Finding recommendation:

`Delete, or snapshot then delete, if genuinely unused`

Estimated monthly savings are calculated from the volume size at a flat gp3 rate of $0.08/GB-month. A volume with no size metadata is reported with no estimate rather than a guessed number.

### Elastic IP Scanner

The Elastic IP scanner calls `DescribeAddresses` and flags addresses without an `AssociationId`.

Finding recommendation:

`Release the address if it's genuinely unused`

Estimated monthly savings use a flat rate of $3.60/month, AWS's standard charge for an unassociated Elastic IP.

### EC2 Utilization Scanner

The EC2 scanner examines running instances and retrieves CloudWatch `AWS/EC2` `CPUUtilization` metrics.

Default configuration:

| Setting | Default |
| --- | ---: |
| CPU threshold | 5% |
| Analysis period | 14 days |
| CloudWatch period | 86,400 seconds |

An instance is flagged when its average returned CPU datapoints are below the configured threshold.

Instances with no datapoints in the requested period are skipped because there is not enough information to classify them as underutilized.

Estimated monthly savings use a per-instance-type hourly on-demand rate (covering the common t2/t3/m5 sizes) multiplied by 730 hours/month. An instance type outside that table falls back to a default hourly rate rather than being left unestimated.

---

## Audit Flow

```text
CLI
 │
 ├── Authenticate with AWS
 │
 ├── Discover regions (unless --region is supplied)
 │
 └── For each region
      │
      ├── EBS scanner
      ├── Elastic IP scanner
      └── EC2 + CloudWatch scanner
             │
             ▼
        Combined findings
             │
        ┌────┴────┐
        ▼         ▼
      JSON       CSV
```

A scanner failure in one resource category is converted into a scanner finding so the remaining scanners can continue.

---

## CLI Usage

After installation:

```bash
cloud-auditor --help
```

### Global Options

```text
-p, --profile       AWS profile name
-r, --region        Region to scan
--endpoint-url      Custom AWS-compatible endpoint, e.g. a local moto server
--version           Show the installed version
```

### Check AWS Identity

```bash
cloud-auditor whoami
cloud-auditor --profile production whoami
```

### List Enabled Regions

```bash
cloud-auditor regions
```

### Run an Audit

Scan all regions returned by AWS:

```bash
cloud-auditor audit
```

Scan a specific region:

```bash
cloud-auditor --region ap-south-1 audit
```

Use a named AWS profile:

```bash
cloud-auditor --profile production audit
```

The CLI option is `--region`, singular. The repository does not currently expose a `--regions` comma-separated option.

---

## Reports

### JSON

JSON export is implemented:

```bash
cloud-auditor report --format json
```

Default file:

```text
reports/audit-report.json
```

You can choose another output directory:

```bash
cloud-auditor report --format json --output-dir reports
```

The JSON report includes:

- Generation timestamp
- Regions scanned
- Total finding count
- Finding counts by resource type
- Estimated total monthly savings across all findings
- An overall optimization score (0-100)
- Individual findings, each with its estimated savings and risk level

### CSV

CSV export is implemented:

```bash
cloud-auditor report --format csv
```

Default file:

```text
reports/audit-report.csv
```

The CSV contains one row per finding, with columns derived directly from the `Finding` fields:

```text
resource_id
resource_type
region
issue
recommendation
metadata
estimated_monthly_savings
risk_level
```

### Terminal Report

Terminal export is implemented. It prints the same table the `audit` command shows, directly to the console:

```bash
cloud-auditor report --format terminal
```

No file is written, and `--output-dir` is ignored for this format. The table includes resource ID, type, region, issue, recommendation, estimated monthly savings, and risk level for every finding. With zero findings it prints a clean "No audit findings detected." message instead of an empty table.

---

## Cleanup

`cloud-auditor cleanup` finds unattached EBS volumes and unassociated Elastic IPs and can delete them -- the only two resource types it will ever act on.

### What it does NOT do

EC2 instances are never touched by this command, under any flag. Stopping or resizing a running instance carries more operational risk than deleting an orphaned volume or releasing an idle IP -- an instance flagged as low-CPU may still be serving traffic. Automated EC2 remediation is not implemented.

### Dry run (default)

```bash
cloud-auditor cleanup
```

Scans, shows exactly which EBS volumes and Elastic IPs would be deleted, and deletes nothing. Any EC2 findings in the same scan are noted as not eligible for automated cleanup, not silently dropped.

### Execute

```bash
cloud-auditor cleanup --execute
```

Runs the same dry-run preview, then asks for an explicit `y`/`N` confirmation before deleting anything. Only a literal `y` proceeds; anything else aborts with nothing deleted. Deletion happens resource-by-resource -- if one fails (e.g. it was already deleted elsewhere), the error is reported and the rest still proceed.

### Cleanup audit log

Every confirmed `cleanup --execute` run appends a record of what it attempted to `logs/cleanup-audit.jsonl`, one JSON object per line:

```json
{"timestamp": "2026-10-12T18:30:56.364246+00:00", "resource_id": "vol-dbbfb1888962a3a7f", "resource_type": "EBS Volume", "region": "us-east-1", "status": "deleted", "error": null}
```

Each line records the resource ID, resource type, region, outcome (`deleted` or `error`, with the error message if one occurred), and a UTC timestamp. The log is append-only -- it is never truncated or overwritten, so it accumulates a full history across every `--execute` run. The `logs/` directory is created automatically if it doesn't exist.

The log is only written when `cleanup --execute` actually runs a deletion attempt (i.e. after `y` is confirmed). A dry run, or an aborted confirmation, writes nothing.

---

## Configuration

The repository currently uses `config/config.yaml` for audit settings.

Current configuration:

```yaml
aws:
  profile: default
  regions:
    - ap-south-1
    - us-east-1

audit:
  ec2:
    enabled: true
    cpu_threshold: 5
    period_days: 14
  ebs:
    enabled: true
  elastic_ip:
    enabled: true

report:
  output_directory: reports
  formats:
    - json
    - csv
```

The scanner aggregator reads the `audit` section and respects each scanner's `enabled` setting.

The CLI's `--region` option takes precedence over automatic region discovery for that invocation.

---

## Local Development with moto

The test suite uses `moto` to emulate AWS services locally.

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

The repository's automated tests use `moto`'s `mock_aws` support, so most tests do not require a live AWS account.

A standalone moto server can also be used when you want to exercise the CLI against an AWS-compatible local endpoint.

For example:

```bash
pip install "moto[server]>=5.0"
moto_server -p 5000
```

Then:

```bash
cloud-auditor --endpoint-url http://localhost:5000 whoami
cloud-auditor --endpoint-url http://localhost:5000 regions
```

When a custom endpoint is supplied and no credentials are available, the project creates a session with test credentials so local emulation can run without real AWS secrets.

---

## Testing

Run the test suite with:

```bash
pytest
```

Verbose mode:

```bash
pytest -v
```

The repository currently contains tests covering:

- Region discovery
- AWS identity verification
- Configuration loading and defaults
- EBS scanning
- Elastic IP scanning
- EC2/CloudWatch utilization scanning
- Scanner aggregation and failure isolation
- Audit command behavior
- JSON reporting
- CSV reporting
- Audit integration with mocked AWS resources

No real AWS resources are required for the automated test suite.

### Continuous Integration

A GitHub Actions workflow (`.github/workflows/tests.yml`) runs the full test suite on every push and pull request to `main`, across Python 3.10, 3.11, and 3.12. No AWS credentials are configured or required in CI, since the suite runs entirely against `moto`. See the Tests badge at the top of this README for current status.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/3000sagar/Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-.git
cd Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the CLI locally

```bash
pip install -e .
```

Verify:

```bash
cloud-auditor --help
```

---

## Standalone Executable

For environments without Python installed, the CLI can be bundled into a single standalone executable with PyInstaller. No install step, no virtual environment -- just run the binary.

### Building

Install the dev dependencies (includes PyInstaller), then build:

```bash
pip install -r requirements-dev.txt
pyinstaller --onefile --name cloud-auditor --collect-all boto3 --collect-all botocore cloud_auditor/__main__.py
```

The `--collect-all boto3 --collect-all botocore` flags are required, not optional -- PyInstaller does not automatically bundle Boto3/Botocore's service-definition data files (the JSON files describing every AWS API call). Without them, the executable launches and `--help` works fine, but every actual AWS call fails. The build output is `dist/cloud-auditor.exe` (Windows) or `dist/cloud-auditor` (Linux/macOS).

### Verifying

The build was manually verified end-to-end against a local `moto_server`, with the Python virtual environment fully deactivated, confirming the executable is genuinely standalone:

```text
cloud-auditor.exe --endpoint-url http://localhost:5000 --region us-east-1 whoami
cloud-auditor.exe --endpoint-url http://localhost:5000 --region us-east-1 regions
cloud-auditor.exe --endpoint-url http://localhost:5000 --region us-east-1 audit
```

`audit` in particular exercises the exact code path (`DescribeVolumes`) that depends on the bundled Botocore service data, so a successful finding confirms the data-bundling flags worked correctly.

`build/`, `dist/`, and the generated `.spec` file are git-ignored -- they're machine-specific build output, not source. Anyone can reproduce the executable locally with the command above.

---

## AWS Permissions

For normal read-only auditing, the scanners and region discovery use AWS API calls corresponding to:

```text
ec2:DescribeInstances
ec2:DescribeVolumes
ec2:DescribeAddresses
ec2:DescribeRegions
cloudwatch:GetMetricStatistics
sts:GetCallerIdentity
```

Cleanup permissions:

```text
ec2:DeleteVolume
ec2:ReleaseAddress
```

are required only if you run `cleanup --execute`. The default `cleanup` dry run, and every other command, only needs the read-only permissions listed above.

Use least-privilege credentials and never commit AWS secrets to source control.

---

## Project Structure

The repository currently looks like this:

```text
Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-/
├── .github/
│   └── workflows/
│       └── tests.yml
├── cloud_auditor/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── audit/
│   │   └── orchestrator.py
│   ├── auth/
│   │   └── aws.py
│   ├── scanners/
│   │   ├── base.py
│   │   ├── aggregator.py
│   │   ├── ebs.py
│   │   ├── ec2.py
│   │   └── elastic_ip.py
│   ├── analysis/
│   │   ├── utilization.py
│   │   └── recommendations.py
│   ├── cleanup/
│   │   ├── executor.py
│   │   └── audit_log.py
│   ├── reporting/
│   │   ├── json_report.py
│   │   ├── csv_report.py
│   │   └── rich_report.py
│   └── utils/
│       ├── config.py
│       ├── regions.py
│       └── retry.py
├── config/
│   └── config.yaml
├── reports/
│   └── .gitkeep
├── tests/
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Tech Stack

### Application

- Python 3.10+
- Typer
- Rich
- Boto3
- PyYAML

### Testing

- pytest
- moto

### Packaging

- Setuptools
- PyInstaller (standalone executable builds)

### CI

- GitHub Actions

---

## Roadmap

### Phase 1 — AWS Foundation

- [x] Project architecture
- [x] Typer CLI
- [x] AWS authentication
- [x] AWS identity verification
- [x] AWS region discovery
- [x] Retry configuration

### Phase 2 — Audit Engine

- [x] Unattached EBS detection
- [x] Unassociated Elastic IP detection
- [x] EC2 utilization analysis
- [x] CloudWatch integration
- [x] Multi-region scanning

### Phase 3 — Reporting and Analysis

- [x] JSON export
- [x] CSV export
- [x] Rich terminal report export
- [x] Cost-saving recommendations
- [x] Optimization scoring

### Phase 4 — Cleanup

- [x] Dry-run mode
- [x] Explicit confirmation workflow
- [x] Safe EBS cleanup
- [x] Safe Elastic IP cleanup
- [x] Cleanup audit logs

### Phase 5 — Distribution and CI

- [x] Automated unit/integration-style tests with moto
- [ ] Additional live-AWS integration tests -- blocked: no AWS free tier remaining to test against
- [x] PyInstaller packaging
- [x] CI/CD
- [ ] PyPI/internal package distribution

---

## Important Notes

### No fake live-output claims

Examples shown in this README are command examples or data shapes, not claims about a particular AWS account.

Actual findings depend on the AWS account, selected regions, configured thresholds, and available CloudWatch datapoints at runtime.

### Cost estimates

Estimated monthly savings are flat-rate approximations (a fixed EBS $/GB rate, a fixed Elastic IP rate, and a per-instance-type or default EC2 hourly rate), not figures pulled from AWS Cost Explorer or an account's actual billing data. They do not account for Reserved Instances, Savings Plans, negotiated discounts, or region-specific pricing differences. Treat them as a rough prioritization signal, not an invoice.

### Optimization score

The 0-100 optimization score is NOT a percentage of wasted spend -- the tool has no access to actual AWS billing data, so no such percentage can be honestly computed. It's a penalty-based score: 100 means a clean scan, and each finding subtracts points weighted by its risk level (High: -5, Medium: -2, Low: -1), floored at 0. It's a relative measure of how much unaddressed risk is sitting in the account, not a dollar or percentage figure.

### Cleanup safety

`cleanup --execute` permanently deletes AWS resources after an explicit confirmation prompt -- there is no undo. It only ever acts on EBS volumes and Elastic IPs; EC2 instances are never deleted, stopped, or resized by this tool. Verify the dry-run output carefully before confirming.

### CloudWatch window

The current EC2 scanner queries a configurable number of days, with a default of 14 days. It calculates the average from the datapoints returned by CloudWatch. It does not guarantee that exactly 14 daily datapoints exist.

### Safety

`cleanup --execute` can modify AWS resources -- see the Cleanup section and the Cleanup safety note above. Production resources should only be deleted after reviewing the dry-run findings, verifying nothing still depends on them, confirming the target account/region, and using least-privilege IAM credentials.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

---

## Author

**Sagar, Aditya**

Built with Python, AWS, Boto3, Typer, Rich, PyYAML, pytest, and moto.