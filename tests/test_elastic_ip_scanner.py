"""Tests for the Elastic IP scanner against a mocked AWS backend."""

from moto import mock_aws

from cloud_auditor.auth.aws import create_session
from cloud_auditor.scanners.elastic_ip import scan_unassociated_addresses


@mock_aws
def test_finds_unassociated_address():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")

    # An unassociated Elastic IP -- should be flagged.
    orphaned = ec2.allocate_address(Domain="vpc")

    # An associated Elastic IP -- should NOT be flagged.
    instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]
    associated = ec2.allocate_address(Domain="vpc")
    ec2.associate_address(
        AllocationId=associated["AllocationId"], InstanceId=instance["InstanceId"]
    )

    findings = scan_unassociated_addresses(session, region="us-east-1")
    found_ids = {f.resource_id for f in findings}

    assert orphaned["AllocationId"] in found_ids
    assert associated["AllocationId"] not in found_ids


@mock_aws
def test_no_addresses_returns_empty_list():
    session = create_session(region="us-east-1")
    findings = scan_unassociated_addresses(session, region="us-east-1")
    assert findings == []