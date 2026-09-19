# ☁️ Cloud Infrastructure Auditor & Cost Optimizer

> **A professional-grade Python CLI for auditing AWS infrastructure, identifying waste and misconfigurations, estimating potential cost savings, and safely cleaning up unused cloud resources.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Boto3-orange?logo=amazon-aws)](https://aws.amazon.com/sdk-for-python/)
[![CLI](https://img.shields.io/badge/CLI-Typer-009688)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-purple)](https://rich.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🚧 Project Status

**Week 1 complete.** CLI scaffolding, AWS authentication, region discovery, and retry/rate-limit handling are implemented and tested (see Phase 1 in the Roadmap), plus a `whoami` command for checking which identity you're authenticated as. `audit`, `report`, and `cleanup` are registered commands that currently return "not yet implemented" — their real logic lands in Weeks 2-3. The Roadmap section is the source of truth for what's actually done.

**Scope: AWS only.** GCP/Azure support is explicitly out of scope for this build.

---

## 📌 Overview

**Cloud Infrastructure Auditor & Cost Optimizer** is a command-line tool designed for **DevOps, Cloud Engineering, and FinOps teams** to automatically inspect cloud infrastructure and identify resources that may be unnecessarily increasing operational costs.

The application connects securely to AWS, scans resources across regions, analyzes utilization and configuration, and generates actionable cost-optimization reports.

It also provides **safe cleanup operations** using a `dry-run` mode and explicit confirmation before making destructive changes.

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

### Planned Checks

| Resource      | Audit                            |
| ------------- | -------------------------------- |
| EC2 Instances | Detect low CPU utilization       |
| EBS Volumes   | Detect unattached volumes        |
| Elastic IPs   | Detect unassociated Elastic IPs  |
| AWS Regions   | Scan multiple configured regions |
| CloudWatch    | Analyze EC2 utilization metrics  |

### EC2 Underutilization

The tool identifies EC2 instances with sustained CPU utilization below a configurable threshold.

Default rule:

```text
CPU Utilization < 5%
Analysis Period = 14 Days
```

This helps identify instances that may be oversized or no longer required.

---

# 💰 Cost Optimization

The tool converts audit findings into actionable cost-saving recommendations.

Target report format:

```text
┌──────────────────────────────────────────────────────────────┐
│                  COST OPTIMIZATION REPORT                    │
├───────────────────────┬─────────────┬────────────────────────┤
│ Resource              │ Issue       │ Recommendation         │
├───────────────────────┼─────────────┼────────────────────────┤
│ vol-0abc123           │ Unattached  │ Delete EBS volume      │
│ eipalloc-xyz          │ Unused      │ Release Elastic IP     │
│ i-0def456             │ <5% CPU     │ Review / downsize EC2  │
└───────────────────────┴─────────────┴────────────────────────┘
```

*(Example format — not live output.)*

The generated report can contain:

* Resource ID
* Resource type
* Region
* Current configuration
* Detected issue
* Utilization information
* Recommended action
* Estimated savings
* Risk level

> **Note:** Cost estimates are recommendations and should be verified against the AWS Billing/Cost Explorer data before making infrastructure changes.

---

# 🛡️ Safe Cleanup

Infrastructure cleanup can be dangerous.

This project therefore separates **auditing** from **execution**.

### Dry Run

Preview the actions without modifying AWS resources:

```bash
cloud-auditor cleanup --dry-run
```

Example:

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

### Execute

Actual cleanup requires explicit confirmation:

```bash
cloud-auditor cleanup --execute
```

The tool should never silently delete resources.

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │       CLI User      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Typer CLI Layer  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              Authentication    Audit Engine     Reporting
                    │               │               │
                    ▼               ▼               ▼
               AWS Profiles      EC2 Scanner      Rich Tables
               IAM Roles         EBS Scanner      JSON
                                 EIP Scanner      CSV
                                      │
                                      ▼
                              ┌───────────────┐
                              │  CloudWatch   │
                              │    Metrics    │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ Recommendations│
                              └───────┬───────┘
                                      │
                             ┌────────┴────────┐
                             ▼                 ▼
                         Dry Run            Execute
                             │                 │
                             ▼                 ▼
                         Preview         AWS Resources
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

### Packaging

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
│   ├── auth/
│   │   ├── __init__.py
│   │   └── aws.py
│   │
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── ec2.py
│   │   ├── ebs.py
│   │   ├── elastic_ip.py
│   │   └── base.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── utilization.py
│   │   └── recommendations.py
│   │
│   ├── cleanup/
│   │   ├── __init__.py
│   │   └── executor.py
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── rich_report.py
│   │   ├── json_report.py
│   │   └── csv_report.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── regions.py
│       └── retry.py
│
├── tests/
│   ├── test_ec2.py
│   ├── test_ebs.py
│   ├── test_elastic_ip.py
│   └── test_cleanup.py
│
├── config/
│   └── config.yaml
│
├── reports/
│
├── .gitignore
├── requirements.txt
├── setup.py
├── pyproject.toml
├── LICENSE
└── README.md
```

> The structure may evolve as the project develops.

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cloud-infrastructure-auditor.git

cd cloud-infrastructure-auditor
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Install the CLI locally

```bash
pip install -e .
```

Verify the installation:

```bash
cloud-auditor --help
```

---

# 🔐 AWS Authentication

The application uses standard AWS authentication mechanisms provided by **Boto3**. It does **not** require hardcoding AWS credentials inside the application.

### Option 1 — AWS CLI Profile

```bash
aws configure
cloud-auditor audit --profile default
```

### Option 2 — Named AWS Profile

```bash
aws configure --profile production
cloud-auditor audit --profile production
```

### Option 3 — IAM Role

When running on AWS infrastructure such as EC2, the application can use the attached IAM role through the standard AWS credential provider chain.

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

Cleanup operations require additional, separately controlled permissions, e.g.:

```text
ec2:DeleteVolume
ec2:ReleaseAddress
```

> **Recommendation:** Use a read-only IAM policy for normal auditing and a separately controlled role/policy for cleanup operations.

Never commit AWS credentials, access keys, secret keys, or `.env` files to GitHub.

---

# 🧪 Local Development (No Live AWS Account Required)

This project is developed and tested against a local AWS emulation layer using **moto**, not a live AWS account. This removes cost risk entirely during development and lets the 14-day CloudWatch utilization window be simulated instantly instead of waiting on real time.

### Run a local AWS mock server

```bash
pip install moto[server]
moto_server -p 5000
```

### Point the CLI at it

```bash
cloud-auditor --endpoint-url http://localhost:5000 whoami
cloud-auditor --endpoint-url http://localhost:5000 regions
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
  -p, --profile        AWS profile name
  -r, --region          Default region
  --endpoint-url         Point at a local moto server for development
  --version              Show version and exit

Commands:
  whoami      Show which AWS identity the tool is authenticated as
  regions     List the AWS regions enabled for this account
  audit       Scan cloud infrastructure
  report      Generate audit reports
  cleanup     Preview or execute cleanup operations
```

## 🙋 Check Your Identity

```bash
cloud-auditor whoami
cloud-auditor --profile production whoami
```

Useful as a sanity check before running an audit against the wrong account.

## 🔎 Run an Audit

```bash
cloud-auditor audit
cloud-auditor audit --profile production
cloud-auditor audit --region ap-south-1
cloud-auditor audit --regions ap-south-1,us-east-1,eu-west-1
```

---

# 📊 Generate Reports

### JSON

```bash
cloud-auditor report --format json
```

### CSV

```bash
cloud-auditor report --format csv
```

### Terminal

```bash
cloud-auditor report --format terminal
```

Rich terminal tables provide an easy-to-read overview of detected issues.

---

# 🧹 Cleanup Workflow

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

---

# 🧪 Testing

The project uses `pytest` for automated testing. AWS services are mocked using **moto**, both during automated tests and during day-to-day development (see Local Development above) — no real AWS account is used at any point in the build.

```bash
pytest
pytest -v
```

---

# 📦 Build Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile cloud_auditor/cli.py
```

Output: `dist/cloud-auditor`

---

# 📈 Example Audit Results

```text
╭────────────────────────────────────────────────────────────────────╮
│                   CLOUD INFRASTRUCTURE AUDIT                      │
├───────────────┬──────────────┬────────────┬───────────────────────┤
│ Resource      │ Region       │ Finding    │ Recommendation        │
├───────────────┼──────────────┼────────────┼───────────────────────┤
│ vol-123456    │ ap-south-1   │ Unattached │ Delete / Review       │
│ eip-789012    │ ap-south-1   │ Unused     │ Release               │
│ i-abcdef123   │ us-east-1    │ <5% CPU    │ Downsize / Terminate  │
╰───────────────┴──────────────┴────────────┴───────────────────────╯

Potential Monthly Savings: $XX.XX

Resources Audited: NN
Issues Found:       N
Optimization Score: NN%
```

*(Illustrative target format — not actual output. Will be replaced with real results once the audit engine runs.)*

---

# 🗺️ Development Roadmap

## Phase 1 — AWS Foundation

* [x] Project architecture
* [x] Typer CLI
* [x] AWS authentication
* [x] AWS region discovery
* [x] Retry/rate-limit handling

## Phase 2 — Audit Engine

* [ ] Unattached EBS detection
* [ ] Unassociated Elastic IP detection
* [ ] EC2 utilization analysis
* [ ] CloudWatch integration
* [ ] Multi-region scanning

## Phase 3 — Reporting

* [ ] Rich terminal reports
* [ ] JSON export
* [ ] CSV export
* [ ] Cost-saving recommendations
* [ ] Optimization scoring

## Phase 4 — Cleanup

* [ ] Dry-run mode
* [ ] Confirmation workflow
* [ ] Safe EBS cleanup
* [ ] Safe Elastic IP cleanup
* [ ] Cleanup audit logs

## Phase 5 — Quality & Distribution

* [ ] Unit/local-dev tests with moto
* [ ] Integration tests
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
* Aggregate audit results.

### Week 3 — Reporting & Cleanup

* Build Rich terminal reports.
* Add JSON export.
* Add CSV export.
* Implement recommendations.
* Implement dry-run functionality.
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

The application should:

* Never store AWS secret keys in source code.
* Use the AWS credential provider chain.
* Support IAM roles.
* Follow least-privilege IAM policies.
* Require explicit confirmation for destructive operations.
* Provide a dry-run mode.
* Avoid logging sensitive credentials.
* Validate resource IDs before cleanup.
* Handle AWS API failures safely.

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

**Do not blindly execute cleanup recommendations.**

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

**Sagar**

Built with Python, AWS, Boto3, Typer, and Rich.