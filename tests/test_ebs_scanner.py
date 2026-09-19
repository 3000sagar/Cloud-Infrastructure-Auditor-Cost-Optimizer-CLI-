"""Tests for the EBS unattached-volume scanner against a mocked backend."""

from moto import mock_aws

from cloud_auditor.auth.aws import create_session
from cloud_auditor.scanners.ebs import scan_unattached_volumes


@mock_aws
def test_finds_unattached_volume():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")

    # An unattached volume -- should be flagged.
    orphaned = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    # An attached volume -- should NOT be flagged. Needs a running
    # instance to attach to.
    instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]
    attached = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    ec2.attach_volume(
        VolumeId=attached["VolumeId"],
        InstanceId=instance["InstanceId"],
        Device="/dev/sdf",
    )

    findings = scan_unattached_volumes(session, region="us-east-1")
    found_ids = {f.resource_id for f in findings}

    assert orphaned["VolumeId"] in found_ids
    assert attached["VolumeId"] not in found_ids


@mock_aws
def test_no_volumes_returns_empty_list():
    session = create_session(region="us-east-1")
    findings = scan_unattached_volumes(session, region="us-east-1")
    assert findings == []