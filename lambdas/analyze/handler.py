import json

import boto3


lambda_client = boto3.client("lambda")


def parse_body(body):
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body
    return body


def invoke_lambda(function_name, payload):
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    return json.loads(response["Payload"].read().decode("utf-8"))


def lambda_handler(event, context):
    # CORS preflight 대응
    method = event.get("requestContext", {}).get("http", {}).get("method")
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
            },
            "body": "",
        }

    # API Gateway / 직접 테스트 둘 다 대응
    if "body" in event and isinstance(event["body"], str):
        try:
            request_body = json.loads(event["body"])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Headers": "content-type",
                    "Access-Control-Allow-Methods": "POST,OPTIONS",
                    "Content-Type": "application/json",
                },
                "body": json.dumps(
                    {"error": "Invalid JSON body"},
                    ensure_ascii=False
                ),
            }
    else:
        request_body = event

    instance_id = request_body.get("instance_id")

    if not instance_id:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {"error": "instance_id is required"},
                ensure_ascii=False
            ),
        }

    # 1) usage_metrics 호출 → 실제 instance_type, cpu_avg 가져옴
    usage_result = invoke_lambda("usage-metrics", {"instance_id": instance_id})
    usage_status = usage_result.get("statusCode", 500)
    usage_body = parse_body(usage_result.get("body", {}))

    if usage_status != 200:
        return {
            "statusCode": usage_status,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps(usage_body, ensure_ascii=False),
        }

    cpu_avg = usage_body.get("cpu_avg", 0.0)
    instance_type = usage_body.get("instance_type", "unknown")

    # 2) cost_collector 호출
    cost_result = invoke_lambda("cost-collector", {})
    cost_status = cost_result.get("statusCode", 500)
    cost_body = parse_body(cost_result.get("body", []))

    if cost_status != 200:
        return {
            "statusCode": cost_status,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps(cost_body, ensure_ascii=False),
        }

    monthly_cost = 0.0
    if isinstance(cost_body, list):
        for item in cost_body:
            if item.get("service") == "Amazon Elastic Compute Cloud - Compute":
                try:
                    monthly_cost = float(item.get("amount", 0))
                except (TypeError, ValueError):
                    monthly_cost = 0.0
                break

    # 3) recommendation 호출 → 실제 instance_type 전달
    recommendation_result = invoke_lambda(
        "recommendation",
        {
            "instance_type": instance_type,
            "cpu_avg": cpu_avg,
            "monthly_cost": monthly_cost,
        },
    )
    recommendation_status = recommendation_result.get("statusCode", 500)
    recommendation_body = parse_body(recommendation_result.get("body", {}))

    if recommendation_status != 200:
        return {
            "statusCode": recommendation_status,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps(recommendation_body, ensure_ascii=False),
        }

    final_result = {
        "instance_id": instance_id,
        "instance_type": instance_type,
        "cpu_avg": cpu_avg,
        "monthly_cost": monthly_cost,
        "recommendation": recommendation_body,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Headers": "content-type",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Content-Type": "application/json",
        },
        "body": json.dumps(final_result, ensure_ascii=False),
    }