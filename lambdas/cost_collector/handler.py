import boto3
from datetime import date, timedelta


def lambda_handler(event, context):
    ce = boto3.client("ce", region_name="us-east-1")

    end = date.today()
    start = end - timedelta(days=30)

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat()
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"}
        ]
    )

    results = []

    for item in response.get("ResultsByTime", []):
        for group in item.get("Groups", []):
            results.append({
                "service": group["Keys"][0],
                "amount": group["Metrics"]["UnblendedCost"]["Amount"],
                "unit": group["Metrics"]["UnblendedCost"]["Unit"]
            })

    return {
        "statusCode": 200,
        "body": results
    }
    
    ##테스트 수정문 반영 확인 version 2