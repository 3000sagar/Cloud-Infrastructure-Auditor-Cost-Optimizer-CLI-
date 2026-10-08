# ☁️ Cloud Infrastructure Auditor & Cost Optimizer

> **A professional-grade Python CLI for auditing AWS infrastructure, identifying waste and misconfigurations, estimating potential cost savings, and safely cleaning up unused cloud resources.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Boto3-orange?logo=amazon-aws)](https://aws.amazon.com/sdk-for-python/)
[![CLI](https://img.shields.io/badge/CLI-Typer-009688)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-purple)](https://rich.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🚧 Project Status

**Weeks 1–2 complete. Week 3 in progress.** Authentication, region discovery, retry handling, all three scanners (EBS, Elastic IP, EC2/CloudWatch), multi-region auditing, cost-estimate recommendations, and JSON/CSV export are implemented and tested. Still to come: a Rich-formatted terminal report file, an optimization score, and the entire `cleanup` command (dry-run and execute). The Roadmap section below is the source of truth for what's actually done — check it before assuming any command works.

**Scope: AWS only.** GCP/Azure support is explicitly out of scope for this build.

---

## 📌 Overview

**Cloud Infrastructure Auditor & Cost Optimizer** is a command-line tool designed for **DevOps, Cloud Engineering, and FinOps teams** to automatically inspect cloud infrastructure and identify resources that may be unnecessarily increasing operational costs.

The application connects securely to AWS, scans resources across regions, analyzes utilization and configuration, and generates actionable cost-optimization reports.

It will also provide **safe cleanup operations** using a `dry-run` mode and explicit confirmation before making destructive changes — see Phase 4 in the Roadmap; this part isn't built yet.

### 🎯 Key Goals

* Identify unused and orphaned cloud resources.
* Detect underutilized infrastructure.
* Highlight potentially misconfigured resources.
* Estimate potential monthly cost savings.
* Provide actionable cleanup recommendations.
* Support multi-region infrastructure auditing.
* Prevent accidental resource deletion through safe execution workflows.

---

# 🚀 Features

## 🔍 Infrastructure Auditing

The auditor scans AWS resources for common sources of cloud waste.

### Implemented Checks

| Resource      | Audit                            |
| ------------- | --------------------------------- |
| EC2 Instances | Detect low CPU utilization        |
| EBS Volumes   | Detect unattached volumes         |
| Elastic IPs   | Detect unassociated Elastic IPs   |
| AWS Regions   | Scan multiple regions (or one, with `--region`) |
| CloudWatch    | Analyze EC2 utilization metrics   |

### EC2 Underutilization

The tool identifies EC2 instances with sustained CPU utilization below a configurable threshold.

Default rule (set in `config/config.yaml`):

```text
CPU Utilization < 5%
Analysis Period = 14 Days
```

This helps identify instances that may be oversized or no longer required.

---

# 💰 Cost Optimization

Every finding is enriched with an estimated monthly savings figure and a risk level (see `cloud_auditor/analysis/recommendations.py`), based on an approximate AWS pricing reference table — not a live pricing API call.

> **Note:** Cost estimates are approximations and should be verified against AWS Billing/Cost Explorer data before making infrastructure changes.

Example — real output from a local test run (`cloud-auditor audit`, against a moto-mocked AWS account with one 100 GB orphaned volume, one unassociated Elastic IP, and one idle `t2.micro` instance):

```text
                                                      Audit findings (3)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Resource ID                ┃ Type         ┃ Region    ┃ Issue                ┃ Recommendation            ┃ Est. $/mo ┃ Risk   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ vol-e26ec1cad8943b5aa      │ EBS Volume   │ us-east-1 │ Unattached           │ Delete, or snapshot then  │ $8.00     │ Low    │
│                            │              │           │                      │ delete, if genuinely      │           │        │
│                            │              │           │                      │ unused                    │           │        │
│ eipalloc-be9beb695a74925cb │ Elastic IP   │ us-east-1 │ Unassociated         │ Release the address if    │ $3.60     │ Low    │
│                            │              │           │                      │ it's genuinely unused     │           │        │
│ i-98d9da34105ec7407        │ EC2 Instance │ us-east-1 │ Avg CPU 1.0% over    │ Review for downsizing or  │ $8.47     │ Medium │
│                            │              │           │ 14d (< 5% threshold) │ termination               │           │        │
└────────────────────────────┴──────────────┴───────────┴──────────────────────┴───────────────────────────┴───────────┴────────┘
```

`report --format json` includes the same per-finding data plus a summary total — for the scenario above, `estimated_total_monthly_savings` is `20.07`.

---

# 🛡️ Safe Cleanup

**Not yet implemented** — the `cleanup` command currently exits with "not implemented yet." The design below is the target behavior (Phase 4 in the Roadmap).

Infrastructure cleanup can be dangerous, so this project separates **auditing** from **execution**.

### Dry Run (target behavior)

```bash
cloud-auditor cleanup --dry-run
```

```text
DRY RUN

The following resources would be removed:

[1] EBS Volume: vol-0123456789
    Region: ap-south-1
    Status: unattached

[2] Elastic IP: 13.233.xxx.xxx
    Region: ap-south-1
    Status: unassociated

No changes have been made.
```

### Execute (target behavior)

```bash
cloud-auditor cleanup --execute
```

The tool should never silently delete resources.

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │       CLI User       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Typer CLI Layer   │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              Authentication   Audit Orchestrator   Reporting
                    │               │               │
                    ▼               ▼               ▼
               AWS Profiles    Scanner Aggregator   Rich Tables
               IAM Roles       (config-driven,      JSON
                                per-region)          CSV
                                     │
                       ┌─────────────┼─────────────┐
                       ▼             ▼             ▼
                 EBS Scanner   EIP Scanner    EC2 Scanner
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │   CloudWatch   │
                                            │    Metrics     │
                                            └───────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │ Recommendations  │
                                           │ (cost + risk)    │
                                           └────────┬─────────┘
                                                    │
                                           ┌────────┴────────┐
                                           ▼                 ▼
                                       Dry Run            Execute
                                           │                 │
                                     (not built yet)   (not built yet)
```

---

# 🧰 Tech Stack

### Core

* **Python 3.10+**
* **Typer** — CLI framework
* **Rich** — terminal UI and formatting

### Cloud

* **Boto3** — AWS SDK

### Data

* **PyYAML** — configuration
* **JSON** — report serialization
* **CSV** — management reports

### Testing

* **pytest**
* **moto** — full local AWS emulation for both development and automated testing

### Packaging (planned, not yet done)

* **Setuptools**
* **PyInstaller**

---

# 📁 Project Structure

```text
cloud-infrastructure-auditor/
│
├── cloud_auditor/
│   ├── __init__.py
│   ├── cli.py
│   │
│   ├── audit/
│   │   ├── __init__.py
│   │   └── orchestrator.py       # multi-region audit orchestration
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   └── aws.py                # session/credential handling, get_client()
│   │
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── base.py               # Finding dataclass, ScannerError
│   │   ├── aggregator.py         # runs all enabled scanners, fault isolation
│   │   ├── ebs.py
│   │   ├── elastic_ip.py
│   │   └── ec2.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── recommendations.py    # cost estimate + risk level
│   │   └── utilization.py        # not yet implemented
│   │
│   ├── cleanup/
│   │   ├── __init__.py
│   │   └── executor.py           # not yet implemented
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   ├── csv_report.py
│   │   └── rich_report.py        # not yet implemented
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py             # loads config/config.yaml
│       ├── regions.py
│       └── retry.py
│
├── tests/
│   ├── test_audit.py
│   ├── test_audit_command.py
│   ├── test_audit_integration.py
│   ├── test_config.py
│   ├── test_csv_report.py
│   ├── test_ebs_scanner.py
│   ├── test_ec2_scanner.py
│   ├── test_elastic_ip_scanner.py
│   ├── test_json_report.py
│   ├── test_recommendations.py
│   ├── test_regions.py
│   └── test_scanner_aggregation.py
│
├── config/
│   └── config.yaml
│
├── reports/
│
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/3000sagar/Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-.git
cd Cloud-Infrastructure-Auditor-Cost-Optimizer-CLI-
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install

Runtime only:

```bash
pip install -e .
```

Runtime plus testing/development tools (pytest, moto):

```bash
pip install -e ".[dev]"
```

Verify the installation:

```bash
cloud-auditor --help
```

---

# 🔐 AWS Authentication

The application uses standard AWS authentication mechanisms provided by **Boto3**. It does **not** require hardcoding AWS credentials inside the application.

`--profile`, `--region`, and `--endpoint-url` are **global** options — they go *before* the command name, not after.

### Option 1 — AWS CLI Profile

```bash
aws configure
cloud-auditor --profile default audit
```

### Option 2 — Named AWS Profile

```bash
aws configure --profile production
cloud-auditor --profile production audit
```

### Option 3 — IAM Role

When running on AWS infrastructure such as EC2, the application can use the attached IAM role through the standard AWS credential provider chain — no flag needed.

---

# 🔑 Required IAM Permissions

The auditor follows the **principle of least privilege**.

Read-only auditing:

```text
ec2:DescribeInstances
ec2:DescribeVolumes
ec2:DescribeAddresses
ec2:DescribeRegions

cloudwatch:GetMetricStatistics
cloudwatch:GetMetricData
```

Cleanup operations (once built) will require additional, separately controlled permissions, e.g.:

```text
ec2:DeleteVolume
ec2:ReleaseAddress
```

> **Recommendation:** Use a read-only IAM policy for normal auditing and a separately controlled role/policy for cleanup operations.

Never commit AWS credentials, access keys, secret keys, or `.env` files to GitHub.

---

# 🧪 Local Development (No Live AWS Account Required)

This project is developed and tested against a local AWS emulation layer using **moto**, not a live AWS account. This removes cost risk entirely during development and lets the 14-day CloudWatch utilization window be simulated instantly instead of waiting on real time.

`moto[server]` is already included via the `dev` extra (`pip install -e ".[dev]"`) — no separate install needed.

### Run a local AWS mock server

```bash
moto_server -p 5000
```

### Point the CLI at it

```bash
cloud-auditor --endpoint-url http://localhost:5000 whoami
cloud-auditor --endpoint-url http://localhost:5000 --region us-east-1 regions
```

`create_session()` automatically supplies dummy credentials when `--endpoint-url` is set and no real credentials are found, so no manual `export AWS_ACCESS_KEY_ID=...` step is needed against moto.

### Seed test resources

Unattached EBS volumes, unassociated Elastic IPs, and EC2 instances are created directly against the mock server via boto3 — no real infrastructure is provisioned, no cost incurred.

### Simulate 14 days of CloudWatch history

A real EC2 instance needs 14 real days of metrics before the utilization scanner has anything to detect. Locally, this is simulated by inserting `put_metric_data` datapoints with backdated timestamps, producing a realistic 14-day low-CPU history in a single call.

> A live AWS pass may still be needed before final submission if the internship's evaluation criteria require proof of a real deployment — this has not yet been confirmed.

---

# 🖥️ CLI Usage

```bash
cloud-auditor --help
```

```text
Usage: cloud-auditor [OPTIONS] COMMAND [ARGS]...

Cloud Infrastructure Auditor & Cost Optimizer

Global options:
  -p, --profile          AWS profile name
  -r, --region            Default region
  --endpoint-url           Point at a local moto server for development
  --version                Show version and exit

Commands:
  whoami      Show which AWS identity the tool is authenticated as
  regions     List the AWS regions enabled for this account
  audit       Scan cloud infrastructure
  report      Generate audit reports
  cleanup     Preview or execute cleanup operations (not yet implemented)
```

## 🙋 Check Your Identity

```bash
cloud-auditor whoami
cloud-auditor --profile production whoami
```

Useful as a sanity check before running an audit against the wrong account.

## 🔎 Run an Audit

Global options go **before** the command:

```bash
cloud-auditor audit
cloud-auditor --profile production audit
cloud-auditor --region ap-south-1 audit
```

With no `--region`, every AWS region enabled for the account is scanned automatically — there's no `--regions` list flag; it's one region (`--region`) or all of them (omit it).

---

# 📊 Generate Reports

`--format` and `--output-dir` are options of the `report` command itself, so they go *after* `report`:

### JSON

```bash
cloud-auditor report --format json
```

### CSV

```bash
cloud-auditor report --format csv
```

### Terminal

Not yet implemented — currently exits with "not implemented yet." Use the `audit` command for a terminal view in the meantime; it prints the same table this will eventually write to a file.

Reports default to the `reports/` directory; override with `--output-dir`:

```bash
cloud-auditor report --format csv --output-dir ./my-reports
```

---

# 🧹 Cleanup Workflow

**Not yet implemented.** Target design:

```text
AUDIT
  ↓
REVIEW FINDINGS
  ↓
GENERATE REPORT
  ↓
DRY RUN
  ↓
USER CONFIRMATION
  ↓
EXECUTE
```

```bash
cloud-auditor cleanup --dry-run
cloud-auditor cleanup --execute
```

The application should request explicit confirmation before destructive operations.

---

# ⚙️ Configuration

`config/config.yaml` controls which scanners run and their thresholds — nothing here requires a code change to adjust:

```yaml
audit:
  ebs:
    enabled: true

  elastic_ip:
    enabled: true

  ec2:
    enabled: true
    cpu_threshold: 5
    period_days: 14
```

A scanner set to `enabled: false` is skipped entirely by the aggregator.

---

# 🧪 Testing

The project uses `pytest`. AWS services are mocked using **moto**, both during automated tests and during day-to-day development (see Local Development above) — no real AWS account is used at any point in the build.

```bash
pytest
pytest -v
```

---

# 📦 Build Standalone Executable

**Not yet attempted.** Target command once Phase 5 is reached:

```bash
pip install pyinstaller
pyinstaller --onefile cloud_auditor/cli.py
```

Output would land in `dist/cloud-auditor`.

---

# 🗺️ Development Roadmap

## Phase 1 — AWS Foundation

* [x] Project architecture
* [x] Typer CLI
* [x] AWS authentication
* [x] AWS region discovery
* [x] Retry/rate-limit handling

## Phase 2 — Audit Engine

* [x] Unattached EBS detection
* [x] Unassociated Elastic IP detection
* [x] EC2 utilization analysis
* [x] CloudWatch integration
* [x] Multi-region scanning

## Phase 3 — Reporting

* [x] Rich terminal report file (`report --format terminal`)
* [x] JSON export
* [x] CSV export
* [x] Cost-saving recommendations
* [ ] Optimization scoring

## Phase 4 — Cleanup

* [ ] Dry-run mode
* [ ] Confirmation workflow
* [ ] Safe EBS cleanup
* [ ] Safe Elastic IP cleanup
* [ ] Cleanup audit logs

## Phase 5 — Quality & Distribution

* [x] Unit/local-dev tests with moto
* [x] Integration tests (CLI end-to-end, via Typer's CliRunner)
* [ ] PyInstaller packaging
* [ ] Documentation
* [ ] CI/CD
* [ ] PyPI/internal package distribution

---

# 📅 4-Week Development Plan

### Week 1 — CLI Architecture & Authentication

* Build Typer command structure.
* Implement AWS authentication.
* Support AWS profiles.
* Implement IAM role support.
* Add region discovery.
* Implement API retry and rate-limit handling.

### Week 2 — Audit Scanners

* Implement EBS scanner.
* Implement Elastic IP scanner.
* Implement EC2 scanner.
* Integrate CloudWatch.
* Detect low-utilization instances.
* Aggregate audit results across regions.

### Week 3 — Reporting & Cleanup

* Add JSON export.
* Add CSV export.
* Implement cost-saving recommendations.
* Build a Rich terminal report file.
* Implement dry-run cleanup.
* Implement safe cleanup execution.

### Week 4 — Testing & Distribution

* Add moto-based AWS tests.
* Improve error handling.
* Package using PyInstaller.
* Prepare documentation.
* Perform user acceptance testing.
* Prepare release.

---

# 🔒 Security Considerations

The application:

* Never stores AWS secret keys in source code.
* Uses the AWS credential provider chain.
* Supports IAM roles.
* Follows least-privilege IAM policies.
* Will require explicit confirmation for destructive operations (once `cleanup` is built).
* Avoids logging sensitive credentials.
* Handles AWS API failures safely (fault-isolated per scanner -- one failure doesn't abort the audit).

Never commit:

```text
.env
credentials
access keys
secret keys
private keys
AWS configuration containing secrets
```

---

# ⚠️ Disclaimer

This project is intended to assist with cloud infrastructure auditing and cost optimization.

**Do not blindly execute cleanup recommendations** once that feature exists.

Before deleting or modifying production resources:

1. Review the audit report.
2. Verify the resource is genuinely unused.
3. Check dependencies.
4. Run the cleanup in `--dry-run` mode.
5. Confirm the target AWS account and region.
6. Use appropriate IAM permissions.
7. Maintain backups where necessary.

The authors are not responsible for infrastructure damage, service interruption, data loss, or unexpected cloud charges caused by incorrect configuration or execution.

---

# 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

# 👨‍💻 Author

**Sagar, Aditya**

Built with Python, AWS, Boto3, Typer, and Rich.