# â˜ï¸ Cloud Infrastructure Auditor & Cost Optimizer

> **A professional-grade Python CLI for auditing AWS infrastructure, identifying waste and misconfigurations, estimating potential cost savings, and safely cleaning up unused cloud resources.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Boto3-orange?logo=amazon-aws)](https://aws.amazon.com/sdk-for-python/)
[![CLI](https://img.shields.io/badge/CLI-Typer-009688)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-purple)](https://rich.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ðŸš§ Project Status

**Week 1 complete.** CLI scaffolding, AWS authentication, region discovery, and retry/rate-limit handling are implemented and tested (see Phase 1 in the Roadmap), plus a `whoami` command for checking which identity you're authenticated as. `audit`, `report`, and `cleanup` are registered commands that currently return "not yet implemented" â€” their real logic lands in Weeks 2-3. The Roadmap section is the source of truth for what's actually done.

**Scope: AWS only.** GCP/Azure support is explicitly out of scope for this build.

---

## ðŸ“Œ Overview

**Cloud Infrastructure Auditor & Cost Optimizer** is a command-line tool designed for **DevOps, Cloud Engineering, and FinOps teams** to automatically inspect cloud infrastructure and identify resources that may be unnecessarily increasing operational costs.

The application connects securely to AWS, scans resources across regions, analyzes utilization and configuration, and generates actionable cost-optimization reports.

It also provides **safe cleanup operations** using a `dry-run` mode and explicit confirmation before making destructive changes.

### ðŸŽ¯ Key Goals

* Identify unused and orphaned cloud resources.
* Detect underutilized infrastructure.
* Highlight potentially misconfigured resources.
* Estimate potential monthly cost savings.
* Provide actionable cleanup recommendations.
* Support multi-region infrastructure auditing.
* Prevent accidental resource deletion through safe execution workflows.

---

# ðŸš€ Features

## ðŸ” Infrastructure Auditing

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

# ðŸ’° Cost Optimization

The tool converts audit findings into actionable cost-saving recommendations.

Target report format:

```text
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  COST OPTIMIZATION REPORT                    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Resource              â”‚ Issue       â”‚ Recommendation         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ vol-0abc123           â”‚ Unattached  â”‚ Delete EBS volume      â”‚
â”‚ eipalloc-xyz          â”‚ Unused      â”‚ Release Elastic IP     â”‚
â”‚ i-0def456             â”‚ <5% CPU     â”‚ Review / downsize EC2  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

*(Example format â€” not live output.)*

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

# ðŸ›¡ï¸ Safe Cleanup

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

# ðŸ—ï¸ Architecture

```text
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚       CLI User      â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚    Typer CLI Layer  â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚               â”‚               â”‚
                    â–¼               â–¼               â–¼
              Authentication    Audit Engine     Reporting
                    â”‚               â”‚               â”‚
                    â–¼               â–¼               â–¼
               AWS Profiles      EC2 Scanner      Rich Tables
               IAM Roles         EBS Scanner      JSON
                                 EIP Scanner      CSV
                                      â”‚
                                      â–¼
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚  CloudWatch   â”‚
                              â”‚    Metrics    â”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                                      â”‚
                                      â–¼
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚ Recommendationsâ”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                                      â”‚
                             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”
                             â–¼                 â–¼
                         Dry Run            Execute
                             â”‚                 â”‚
                             â–¼                 â–¼
                         Preview         AWS Resources
```

---

# ðŸ§° Tech Stack

### Core

* **Python 3.10+**
* **Typer** â€” CLI framework
* **Rich** â€” terminal UI and formatting

### Cloud

* **Boto3** â€” AWS SDK

### Data

* **PyYAML** â€” configuration
* **JSON** â€” report serialization
* **CSV** â€” management reports

### Testing

* **pytest**
* **moto** â€” full local AWS emulation for both development and automated testing

### Packaging

* **Setuptools**
* **PyInstaller**

---

# ðŸ“ Project Structure

```text
cloud-infrastructure-auditor/
â”‚
â”œâ”€â”€ cloud_auditor/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ cli.py
â”‚   â”‚
â”‚   â”œâ”€â”€ auth/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ aws.py
â”‚   â”‚
â”‚   â”œâ”€â”€ scanners/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ ec2.py
â”‚   â”‚   â”œâ”€â”€ ebs.py
â”‚   â”‚   â”œâ”€â”€ elastic_ip.py
â”‚   â”‚   â””â”€â”€ base.py
â”‚   â”‚
â”‚   â”œâ”€â”€ analysis/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ utilization.py
â”‚   â”‚   â””â”€â”€ recommendations.py
â”‚   â”‚
â”‚   â”œâ”€â”€ cleanup/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ executor.py
â”‚   â”‚
â”‚   â”œâ”€â”€ reporting/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ rich_report.py
â”‚   â”‚   â”œâ”€â”€ json_report.py
â”‚   â”‚   â””â”€â”€ csv_report.py
â”‚   â”‚
â”‚   â””â”€â”€ utils/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ regions.py
â”‚       â””â”€â”€ retry.py
â”‚
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_ec2.py
â”‚   â”œâ”€â”€ test_ebs.py
â”‚   â”œâ”€â”€ test_elastic_ip.py
â”‚   â””â”€â”€ test_cleanup.py
â”‚
â”œâ”€â”€ config/
â”‚   â””â”€â”€ config.yaml
â”‚
â”œâ”€â”€ reports/
â”‚
â”œâ”€â”€ .gitignore
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ setup.py
â”œâ”€â”€ pyproject.toml
â”œâ”€â”€ LICENSE
â””â”€â”€ README.md
```

> The structure may evolve as the project develops.

---

# âš™ï¸ Installation

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

# ðŸ” AWS Authentication

The application uses standard AWS authentication mechanisms provided by **Boto3**. It does **not** require hardcoding AWS credentials inside the application.

### Option 1 â€” AWS CLI Profile

```bash
aws configure
cloud-auditor audit --profile default
```

### Option 2 â€” Named AWS Profile

```bash
aws configure --profile production
cloud-auditor audit --profile production
```

### Option 3 â€” IAM Role

When running on AWS infrastructure such as EC2, the application can use the attached IAM role through the standard AWS credential provider chain.

---

# ðŸ”‘ Required IAM Permissions

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

# ðŸ§ª Local Development (No Live AWS Account Required)

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

Unattached EBS volumes, unassociated Elastic IPs, and EC2 instances are created directly against the mock server via boto3 â€” no real infrastructure is provisioned, no cost incurred.

### Simulate 14 days of CloudWatch history

A real EC2 instance needs 14 real days of metrics before the utilization scanner has anything to detect. Locally, this is simulated by inserting `put_metric_data` datapoints with backdated timestamps, producing a realistic 14-day low-CPU history in a single call.

> A live AWS pass may still be needed before final submission if the internship's evaluation criteria require proof of a real deployment â€” this has not yet been confirmed.

---

# ðŸ–¥ï¸ CLI Usage

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

## ðŸ™‹ Check Your Identity

```bash
cloud-auditor whoami
cloud-auditor --profile production whoami
```

Useful as a sanity check before running an audit against the wrong account.

## ðŸ”Ž Run an Audit

```bash
cloud-auditor audit
cloud-auditor audit --profile production
cloud-auditor audit --region ap-south-1
cloud-auditor audit --regions ap-south-1,us-east-1,eu-west-1
```

---

# ðŸ“Š Generate Reports

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

# ðŸ§¹ Cleanup Workflow

```text
AUDIT
  â†“
REVIEW FINDINGS
  â†“
GENERATE REPORT
  â†“
DRY RUN
  â†“
USER CONFIRMATION
  â†“
EXECUTE
```

```bash
cloud-auditor cleanup --dry-run
cloud-auditor cleanup --execute
```

The application should request explicit confirmation before destructive operations.

---

# âš™ï¸ Configuration

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

# ðŸ§ª Testing

The project uses `pytest` for automated testing. AWS services are mocked using **moto**, both during automated tests and during day-to-day development (see Local Development above) â€” no real AWS account is used at any point in the build.

```bash
pytest
pytest -v
```

---

# ðŸ“¦ Build Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile cloud_auditor/cli.py
```

Output: `dist/cloud-auditor`

---

# ðŸ“ˆ Example Audit Results

```text
â•­â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•®
â”‚                   CLOUD INFRASTRUCTURE AUDIT                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Resource      â”‚ Region       â”‚ Finding    â”‚ Recommendation        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ vol-123456    â”‚ ap-south-1   â”‚ Unattached â”‚ Delete / Review       â”‚
â”‚ eip-789012    â”‚ ap-south-1   â”‚ Unused     â”‚ Release               â”‚
â”‚ i-abcdef123   â”‚ us-east-1    â”‚ <5% CPU    â”‚ Downsize / Terminate  â”‚
â•°â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•¯

Potential Monthly Savings: $XX.XX

Resources Audited: NN
Issues Found:       N
Optimization Score: NN%
```

*(Illustrative target format â€” not actual output. Will be replaced with real results once the audit engine runs.)*

---

# ðŸ—ºï¸ Development Roadmap

## Phase 1 â€” AWS Foundation

* [x] Project architecture
* [x] Typer CLI
* [x] AWS authentication
* [x] AWS region discovery
* [x] Retry/rate-limit handling

## Phase 2 â€” Audit Engine

* [x] Unattached EBS detection
* [x] Unassociated Elastic IP detection
* [x] EC2 utilization analysis
* [x] CloudWatch integration
* [ ] Multi-region scanning

## Phase 3 â€” Reporting

* [ ] Rich terminal reports
* [x] JSON export
* [x] CSV export
* [ ] Cost-saving recommendations
* [ ] Optimization scoring

## Phase 4 â€” Cleanup

* [ ] Dry-run mode
* [ ] Confirmation workflow
* [ ] Safe EBS cleanup
* [ ] Safe Elastic IP cleanup
* [ ] Cleanup audit logs

## Phase 5 â€” Quality & Distribution

* [ ] Unit/local-dev tests with moto
* [ ] Integration tests
* [ ] PyInstaller packaging
* [ ] Documentation
* [ ] CI/CD
* [ ] PyPI/internal package distribution

---

# ðŸ“… 4-Week Development Plan

### Week 1 â€” CLI Architecture & Authentication

* Build Typer command structure.
* Implement AWS authentication.
* Support AWS profiles.
* Implement IAM role support.
* Add region discovery.
* Implement API retry and rate-limit handling.

### Week 2 â€” Audit Scanners

* Implement EBS scanner.
* Implement Elastic IP scanner.
* Implement EC2 scanner.
* Integrate CloudWatch.
* Detect low-utilization instances.
* Aggregate audit results.

### Week 3 â€” Reporting & Cleanup

* Build Rich terminal reports.
* Add JSON export.
* Add CSV export.
* Implement recommendations.
* Implement dry-run functionality.
* Implement safe cleanup execution.

### Week 4 â€” Testing & Distribution

* Add moto-based AWS tests.
* Improve error handling.
* Package using PyInstaller.
* Prepare documentation.
* Perform user acceptance testing.
* Prepare release.

---

# ðŸ”’ Security Considerations

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

# âš ï¸ Disclaimer

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

# ðŸ“„ License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

# ðŸ‘¨â€ðŸ’» Author

**Sagar**

Built with Python, AWS, Boto3, Typer, and Rich.
