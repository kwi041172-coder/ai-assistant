from .firebase_service import get_all_data

def analyze_data():
    """데이터 분석 및 요약"""
    data_list = get_all_data()

    if not data_list:
        return {
            "period": "데이터 없음",
            "count": 0,
            "metrics": {
                "total": 0,
                "average": 0,
                "max": 0,
                "min": 0
            },
            "trend": "분석 불가"
        }

    ordered_data = sorted(data_list, key=lambda record: record["date"])
    values = [float(record["value"]) for record in ordered_data]
    dates = [record["date"] for record in ordered_data]

    total = sum(values)
    average = total / len(values)
    max_val = max(values)
    min_val = min(values)

    split_idx = len(values) // 2
    if split_idx:
        previous_values = values[:split_idx]
        recent_values = values[split_idx:]
        previous_avg = sum(previous_values) / len(previous_values)
        recent_avg = sum(recent_values) / len(recent_values)
    else:
        previous_avg = recent_avg = average

    if recent_avg > previous_avg * 1.05:
        trend = "상승 추세"
    elif recent_avg < previous_avg * 0.95:
        trend = "하락 추세"
    else:
        trend = "안정적"

    period = f"{dates[0]} ~ {dates[-1]}"

    return {
        "period": period,
        "count": len(data_list),
        "metrics": {
            "total": round(total, 2),
            "average": round(average, 2),
            "max": round(max_val, 2),
            "min": round(min_val, 2)
        },
        "trend": trend
    }