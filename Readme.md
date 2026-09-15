# ☁️ Cloud Infrastructure Auditor & Cost Optimizer

> **A professional-grade Python CLI for auditing AWS infrastructure, identifying waste and misconfigurations, estimating potential cost savings, and safely cleaning up unused cloud resources.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Boto3-orange?logo=amazon-aws)](https://aws.amazon.com/sdk-for-python/)
[![CLI](https://img.shields.io/badge/CLI-Typer-009688)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-purple)](https://rich.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Overview

**Cloud Infrastructure Auditor & Cost Optimizer** is a command-line tool designed for **DevOps, Cloud Engineering, and FinOps teams** to automatically inspect cloud infrastructure and identify resources that may be unnecessarily increasing operational costs.

The application connects securely to cloud providers, scans resources across regions, analyzes utilization and configuration, and generates actionable cost-optimization reports.

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

### Current Checks

| Resource      | Audit                            |
| ------------- | -------------------------------- |
| EC2 Instances | Detect low CPU utilization       |
| EBS Volumes   | Detect unattached volumes        |
| Elastic IPs   | Detect unassociated Elastic IPs  |
| AWS Regions   | Scan multiple configured regions |
| CloudWatch    | Analyze EC2 utilization metrics  |

### EC2 Underutilization

The tool can identify EC2 instances with sustained CPU utilization below a configurable threshold.

Default rule:

```text
CPU Utilization < 5%
Analysis Period = 14 Days
```

This helps identify instances that may be oversized or no longer required.

---

# 💰 Cost Optimization

The tool converts audit findings into actionable cost-saving recommendations.

Example:

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
* **Google Cloud Client Libraries** — planned GCP support

### Data

* **PyYAML** — configuration
* **JSON** — report serialization
* **CSV** — management reports

### Testing

* **pytest**
* **moto** — AWS service mocking

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

The application uses standard AWS authentication mechanisms provided by **Boto3**.

It does **not** require hardcoding AWS credentials inside the application.

### Option 1 — AWS CLI Profile

Configure an AWS profile:

```bash
aws configure
```

Then run:

```bash
cloud-auditor audit --profile default
```

### Option 2 — Named AWS Profile

```bash
aws configure --profile production
```

Run:

```bash
cloud-auditor audit --profile production
```

### Option 3 — IAM Role

When running on AWS infrastructure such as EC2, the application can use the attached IAM role through the standard AWS credential provider chain.

---

# 🔑 Required IAM Permissions

The auditor should follow the **principle of least privilege**.

For read-only auditing, permissions may include:

```text
ec2:DescribeInstances
ec2:DescribeVolumes
ec2:DescribeAddresses
ec2:DescribeRegions

cloudwatch:GetMetricStatistics
cloudwatch:GetMetricData
```

Cleanup operations require additional permissions depending on the resources being modified.

For example:

```text
ec2:DeleteVolume
ec2:ReleaseAddress
```

> **Recommendation:** Use a read-only IAM policy for normal auditing and a separately controlled role/policy for cleanup operations.

Never commit AWS credentials, access keys, secret keys, or `.env` files to GitHub.

---

# 🖥️ CLI Usage

Display available commands:

```bash
cloud-auditor --help
```

Example:

```text
Usage: cloud-auditor [OPTIONS] COMMAND [ARGS]...

Cloud Infrastructure Auditor & Cost Optimizer

Commands:
  audit       Scan cloud infrastructure
  report      Generate audit reports
  cleanup     Preview or execute cleanup operations
  regions     List supported AWS regions
  version     Display application version
```

---

## 🔎 Run an Audit

Scan the default AWS profile:

```bash
cloud-auditor audit
```

Scan a specific profile:

```bash
cloud-auditor audit --profile production
```

Scan a specific region:

```bash
cloud-auditor audit --region ap-south-1
```

Scan multiple regions:

```bash
cloud-auditor audit --regions ap-south-1,us-east-1,eu-west-1
```

---

# 📊 Generate Reports

### JSON

```bash
cloud-auditor report --format json
```

Output:

```text
reports/audit-report.json
```

### CSV

```bash
cloud-auditor report --format csv
```

Output:

```text
reports/audit-report.csv
```

### Terminal

```bash
cloud-auditor report --format terminal
```

Rich terminal tables provide an easy-to-read overview of detected issues.

---

# 🧹 Cleanup Workflow

The recommended workflow is:

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

Example:

```bash
cloud-auditor cleanup --dry-run
```

After reviewing the results:

```bash
cloud-auditor cleanup --execute
```

The application should request explicit confirmation before destructive operations.

---

# ⚙️ Configuration

Configuration can be managed through YAML.

Example:

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

This allows teams to customize scanning behavior without modifying source code.

---

# 🧪 Testing

The project uses `pytest` for automated testing.

AWS services are mocked using **moto**, preventing accidental AWS charges during tests.

Run all tests:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Example:

```text
============================= test session starts =============================

tests/test_ec2.py ........
tests/test_ebs.py ........
tests/test_elastic_ip.py ...
tests/test_cleanup.py .....

============================== 24 passed ==============================
```

---

# 📦 Build Standalone Executable

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the executable:

```bash
pyinstaller --onefile cloud_auditor/cli.py
```

The executable will be generated inside:

```text
dist/
```

Example:

```bash
dist/cloud-auditor
```

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

Resources Audited: 47
Issues Found:       8
Optimization Score: 83%
```

---

# 🌎 Supported Cloud Providers

| Provider     | Status            |
| ------------ | ----------------- |
| AWS          | 🚧 In Development |
| Google Cloud | 🔮 Planned        |
| Azure        | 🔮 Future         |

The architecture is designed to allow additional cloud providers to be integrated through provider-specific scanner modules.

---

# 🗺️ Development Roadmap

## Phase 1 — AWS Foundation

* [x] Project architecture
* [x] Typer CLI
* [ ] AWS authentication
* [ ] AWS region discovery
* [ ] Retry/rate-limit handling

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

* [ ] Unit tests with moto
* [ ] Integration tests
* [ ] PyInstaller packaging
* [ ] Documentation
* [ ] CI/CD
* [ ] PyPI/internal package distribution

## Phase 6 — Multi-Cloud

* [ ] GCP integration
* [ ] GCP resource scanners
* [ ] Unified cloud reporting
* [ ] Cross-cloud cost optimization

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

Security is a core requirement of this project.

### The application should:

* Never store AWS secret keys in source code.
* Use the AWS credential provider chain.
* Support IAM roles.
* Follow least-privilege IAM policies.
* Require explicit confirmation for destructive operations.
* Provide a dry-run mode.
* Avoid logging sensitive credentials.
* Validate resource IDs before cleanup.
* Handle AWS API failures safely.

### Never commit:

```text
.env
credentials
access keys
secret keys
private keys
AWS configuration containing secrets
```

Add sensitive files to `.gitignore`.

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

# 🤝 Contributing

Contributions are welcome.

### 1. Fork the repository

```bash
git clone https://github.com/YOUR_USERNAME/cloud-infrastructure-auditor.git
```

### 2. Create a branch

```bash
git checkout -b feature/new-scanner
```

### 3. Make your changes

Follow the existing project structure and coding conventions.

### 4. Run tests

```bash
pytest
```

### 5. Commit

```bash
git add .

git commit -m "Add new infrastructure scanner"
```

### 6. Push

```bash
git push origin feature/new-scanner
```

Then open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.

---

# 👨‍💻 Author

**Sagar**

Built with Python, AWS, Boto3, Typer, Rich, and a strong obsession with eliminating unnecessary cloud bills. ☁️💸

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

**Cloud waste adds up quietly. This tool is built to make it visible.**
