import boto3
import json

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
        Payload=json.dumps(payload)
    )
    response_payload = json.loads(response["Payload"].read().decode("utf-8"))
    return response_payload


def lambda_handler(event, context):
    # ✅ 브라우저 preflight OPTIONS 요청 처리
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": ""
        }

    # API Gateway / Lambda 콘솔 테스트 둘 다 대응
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
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"error": "Invalid JSON body"}, ensure_ascii=False)
            }
    else:
        request_body = event

    instance_id = request_body.get("instance_id")
    instance_type = request_body.get("instance_type", "t3.large")

    if not instance_id:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": "instance_id is required"}, ensure_ascii=False)
        }

    usage_result = invoke_lambda(
        "usage-metrics",
        {"instance_id": instance_id}
    )
    usage_body = parse_body(usage_result.get("body", {}))
    cpu_avg = usage_body.get("cpu_avg") if isinstance(usage_body, dict) else None

    cost_result = invoke_lambda("cost-collector", {})
    cost_body = parse_body(cost_result.get("body", []))

    monthly_cost = 0.0
    if isinstance(cost_body, list):
        for item in cost_body:
            if item.get("service") == "Amazon Elastic Compute Cloud - Compute":
                try:
                    monthly_cost = float(item.get("amount", 0))
                except (ValueError, TypeError):
                    monthly_cost = 0.0
                break

    recommendation_result = invoke_lambda(
        "recommendation",
        {
            "instance_type": instance_type,
            "cpu_avg": cpu_avg,
            "monthly_cost": monthly_cost
        }
    )
    recommendation_body = parse_body(recommendation_result.get("body", {}))

    final_result = {
        "instance_id": instance_id,
        "instance_type": instance_type,
        "cpu_avg": cpu_avg,
        "monthly_cost": monthly_cost,
        "recommendation": recommendation_body
    }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Headers": "content-type",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Content-Type": "application/json"
        },
        "body": json.dumps(final_result, ensure_ascii=False)
    }
    
        ##깃액션 수정 반영 확인