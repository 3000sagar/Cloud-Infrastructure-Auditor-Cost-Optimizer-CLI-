# Cloud Infrastructure Auditor & Cost Optimizer

> A Python CLI for auditing AWS infrastructure, identifying common sources of cloud waste, and exporting audit findings to JSON or CSV.

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
- Retry/backoff configuration
- Automated tests using `pytest` and `moto`

The following parts are currently **not implemented**:

- Destructive cleanup execution
- Dry-run/confirmation cleanup workflow
- PyInstaller distribution workflow
- CI/CD pipeline
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

## Cleanup Status

Cleanup code is currently a stub.

The repository does **not** currently delete AWS resources, and the CLI command:

```bash
cloud-auditor cleanup
```

reports that cleanup is not implemented.

The intended future workflow is:

```text
AUDIT
  ↓
REVIEW FINDINGS
  ↓
DRY RUN
  ↓
USER CONFIRMATION
  ↓
EXECUTE
```

Do not treat the cleanup examples from older documentation as available functionality on the current `main` branch.

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

Cleanup permissions such as:

```text
ec2:DeleteVolume
ec2:ReleaseAddress
```

are **not required by the current implementation**, because destructive cleanup has not been implemented yet.

Use least-privilege credentials and never commit AWS secrets to source control.

---

## Project Structure

The repository currently looks like this:

```text
Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-/
├── cloud_auditor/
│   ├── __init__.py
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
│   │   └── executor.py
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

PyInstaller is not currently part of the project's declared dependencies or build configuration.

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

- [ ] Dry-run mode
- [ ] Explicit confirmation workflow
- [ ] Safe EBS cleanup
- [ ] Safe Elastic IP cleanup
- [ ] Cleanup audit logs

### Phase 5 — Distribution and CI

- [x] Automated unit/integration-style tests with moto
- [ ] Additional live-AWS integration tests
- [ ] PyInstaller packaging
- [ ] CI/CD
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

### CloudWatch window

The current EC2 scanner queries a configurable number of days, with a default of 14 days. It calculates the average from the datapoints returned by CloudWatch. It does not guarantee that exactly 14 daily datapoints exist.

### Safety

The current `cleanup` command does not modify AWS resources. When destructive functionality is eventually added, production resources should only be modified after reviewing findings, verifying dependencies, checking the target account/region, and using appropriate IAM controls.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

---

## Author

**Sagar, Aditya**

Built with Python, AWS, Boto3, Typer, Rich, PyYAML, pytest, and moto.