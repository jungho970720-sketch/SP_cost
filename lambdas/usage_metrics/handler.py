import json
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # API Gateway / 직접 테스트 둘 다 대응
    if "body" in event and isinstance(event["body"], str):
        try:
            request_body = json.loads(event["body"])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": "Invalid JSON body"},
                    ensure_ascii=False,
                ),
            }
    else:
        request_body = event

    instance_id = request_body.get("instance_id")

    if not instance_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "instance_id is required"},
                ensure_ascii=False,
            ),
        }

    ec2 = boto3.client("ec2")
    cloudwatch = boto3.client("cloudwatch")

    # 1) 인스턴스 존재 여부 확인
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        reservations = response.get("Reservations", [])
        instances = [
            instance
            for reservation in reservations
            for instance in reservation.get("Instances", [])
        ]

        if not instances:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": f"EC2 instance not found: {instance_id}"},
                    ensure_ascii=False,
                ),
            }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("InvalidInstanceID.NotFound", "ValidationError"):
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": f"EC2 instance not found: {instance_id}"},
                    ensure_ascii=False,
                ),
            }

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Failed to validate instance: {str(e)}"},
                ensure_ascii=False,
            ),
        }

    # 2) CloudWatch CPU 조회
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    try:
        metric_response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"],
        )
    except ClientError as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Failed to fetch CloudWatch metrics: {str(e)}"},
                ensure_ascii=False,
            ),
        }

    datapoints = metric_response.get("Datapoints", [])
    datapoints.sort(key=lambda x: x["Timestamp"])

    cpu_values = [point["Average"] for point in datapoints]
    cpu_avg = round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0.0

    result = {
        "instance_id": instance_id,
        "cpu_avg": cpu_avg,
        "datapoints_count": len(datapoints),
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result, ensure_ascii=False),
    }