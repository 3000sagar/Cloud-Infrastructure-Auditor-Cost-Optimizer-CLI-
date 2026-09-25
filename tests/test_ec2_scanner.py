"""Tests for the EC2 low-utilization scanner against a mocked backend."""

import datetime as dt

from moto import mock_aws

from cloud_auditor.auth.aws import create_session
from cloud_auditor.scanners.ec2 import scan_underutilized_instances


def _put_daily_cpu(cloudwatch, instance_id, days, cpu_percent):
    """Seed one CloudWatch CPUUtilization datapoint per day, backdated,
    to simulate a real 14-day history without waiting 14 real days.
    """
    now = dt.datetime.now(dt.timezone.utc)
    for day_offset in range(days):
        timestamp = now - dt.timedelta(days=day_offset)
        cloudwatch.put_metric_data(
            Namespace="AWS/EC2",
            MetricData=[
                {
                    "MetricName": "CPUUtilization",
                    "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
                    "Timestamp": timestamp,
                    "Value": cpu_percent,
                    "Unit": "Percent",
                }
            ],
        )


@mock_aws
def test_flags_instance_with_sustained_low_cpu():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    cloudwatch = session.client("cloudwatch", region_name="us-east-1")

    idle = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]
    busy = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]

    _put_daily_cpu(cloudwatch, idle["InstanceId"], days=14, cpu_percent=2.0)
    _put_daily_cpu(cloudwatch, busy["InstanceId"], days=14, cpu_percent=45.0)

    findings = scan_underutilized_instances(session, region="us-east-1")
    found_ids = {f.resource_id for f in findings}

    assert idle["InstanceId"] in found_ids
    assert busy["InstanceId"] not in found_ids


@mock_aws
def test_instance_with_no_metrics_is_not_flagged():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")

    ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro")

    findings = scan_underutilized_instances(session, region="us-east-1")
    assert findings == []