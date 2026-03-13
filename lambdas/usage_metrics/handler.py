import boto3
from datetime import datetime, timedelta, timezone


def lambda_handler(event, context):
    instance_id = event.get("instance_id")

    if not instance_id:
        return {
            "statusCode": 400,
            "body": "instance_id is required"
        }

    cloudwatch = boto3.client("cloudwatch")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {"Name": "InstanceId", "Value": instance_id}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=["Average"]
    )

    datapoints = response.get("Datapoints", [])
    datapoints.sort(key=lambda x: x["Timestamp"])

    cpu_values = [point["Average"] for point in datapoints]

    cpu_avg = round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else None

    return {
        "statusCode": 200,
        "body": {
            "instance_id": instance_id,
            "cpu_avg": cpu_avg,
            "datapoints_count": len(datapoints)
        }
    }