import json

def lambda_handler(event, context):

    instance_type = event.get("instance_type", "t3.large")
    cpu_avg = event.get("cpu_avg", 0)
    monthly_cost = event.get("monthly_cost", 0)

    recommendation = "유지"
    reason = "현재 상태를 유지합니다."
    expected_saving = 0

    if cpu_avg is not None and cpu_avg < 10:
        recommendation = "다운사이징 검토"
        reason = "최근 평균 CPU 사용률이 10% 미만으로 낮습니다."
        expected_saving = round(monthly_cost * 0.3, 2)

    elif cpu_avg > 80:
        recommendation = "업사이징 검토"
        reason = "CPU 사용률이 높아 성능 문제가 발생할 수 있습니다."

    body = {
        "instance_type": instance_type,
        "cpu_avg": cpu_avg,
        "monthly_cost": monthly_cost,
        "recommendation": recommendation,
        "reason": reason,
        "expected_saving": expected_saving
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }