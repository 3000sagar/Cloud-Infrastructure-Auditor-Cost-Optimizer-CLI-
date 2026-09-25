"""EC2 low-utilization scanner. Not yet implemented (Week 2).

Will use CloudWatch GetMetricData to find instances with sustained
CPU < 5% over a 14-day window (see config/config.yaml for the
threshold and period, both configurable).
""""""EC2 low-utilization scanner."""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError

from cloud_auditor.auth.aws import get_client
from cloud_auditor.scanners.base import Finding, ScannerError

# Matches config/config.yaml's audit.ec2 defaults.
DEFAULT_CPU_THRESHOLD = 5.0
DEFAULT_PERIOD_DAYS = 14


def scan_underutilized_instances(
    session,
    region: str,
    endpoint_url: Optional[str] = None,
    cpu_threshold: float = DEFAULT_CPU_THRESHOLD,
    period_days: int = DEFAULT_PERIOD_DAYS,
) -> List[Finding]:
    """Return a Finding for every running EC2 instance whose average
    CPU utilization over the last `period_days` days is below
    `cpu_threshold`.

    Instances with no CloudWatch datapoints in the window (e.g. just
    launched) are skipped rather than flagged -- there isn't enough
    data yet to call them underutilized either way.
    """
    try:
        ec2 = get_client(session, "ec2", region=region, endpoint_url=endpoint_url)
        cloudwatch = get_client(
            session, "cloudwatch", region=region, endpoint_url=endpoint_url
        )
        instances_response = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
    except (BotoCoreError, ClientError) as exc:
        raise ScannerError(f"Could not scan EC2 instances in {region}: {exc}") from exc

    end_time = dt.datetime.now(dt.timezone.utc)
    start_time = end_time - dt.timedelta(days=period_days)

    findings: List[Finding] = []
    for reservation in instances_response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            try:
                metrics = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=["Average"],
                )
            except (BotoCoreError, ClientError) as exc:
                raise ScannerError(
                    f"Could not fetch CloudWatch metrics for {instance_id}: {exc}"
                ) from exc

            datapoints = metrics["Datapoints"]
            if not datapoints:
                continue

            avg_cpu = sum(dp["Average"] for dp in datapoints) / len(datapoints)
            if avg_cpu < cpu_threshold:
                findings.append(
                    Finding(
                        resource_id=instance_id,
                        resource_type="EC2 Instance",
                        region=region,
                        issue=(
                            f"Avg CPU {avg_cpu:.1f}% over {period_days}d "
                            f"(< {cpu_threshold}% threshold)"
                        ),
                        recommendation="Review for downsizing or termination",
                    )
                )
    return findings