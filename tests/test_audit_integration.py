import boto3
from moto import mock_aws

from cloud_auditor.audit.orchestrator import run_audit


@mock_aws
def test_run_audit_with_fake_aws_resources():
    region = "us-east-1"

    session = boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name=region,
    )

    ec2 = session.client("ec2", region_name=region)

    # Create an unattached EBS volume.
    ec2.create_volume(
        AvailabilityZone="us-east-1a",
        Size=10,
    )

    # Allocate an Elastic IP without associating it with an instance.
    ec2.allocate_address(
        Domain="vpc",
    )

    findings = run_audit(
        session=session,
        regions=[region],
    )

    resource_types = {finding.resource_type for finding in findings}

    assert "EBS Volume" in resource_types
    assert "Elastic IP" in resource_types