"""Vietnamese, deterministic commentary on the exact aggregates shown in the report."""

from crm.models import LeadRequest


def money(value):
    return f"{value:,.0f}".replace(",", ".") + " VNĐ"


def report_insights(data):
    insights = []
    total = sum(row["count"] for row in data.get("lead_tiers", []))
    hot = sum(row["count"] for row in data.get("lead_tiers", []) if row["tier"] == "HOT")
    insights.append({"title": "Ưu tiên cơ hội kinh doanh", "text": (
        f"Có {hot}/{total} yêu cầu đang được xếp HOT ({hot / total:.0%}). "
        "Nên rà soát nhu cầu và lịch liên hệ của nhóm này trước khi tạo việc chăm sóc. "
        "Điểm xếp hạng là quy tắc tham khảo, chưa phải xác suất chốt hợp đồng."
        if total else "Chưa có yêu cầu đủ điều kiện chấm điểm. Cần có lead được phép phân tích và làm mới dữ liệu trước khi xác định nhóm ưu tiên."
    )})
    solutions = data.get("solutions", [])
    labels = dict(LeadRequest.SolutionInterest.choices)
    if solutions:
        top = max(solutions, key=lambda row: row["count"])
        solution_text = (f"{labels.get(top['solution'], top['solution'])} là một trong các nhóm có nhiều yêu cầu nhất, "
                         f"với {top['count']} yêu cầu. Nên chuẩn bị kịch bản khảo sát và demo cho nhóm này. "
                         "Giá trị cơ hội trên biểu đồ dùng mức hợp đồng giả định, không phải doanh thu đã ghi nhận.")
    else:
        solution_text = "Chưa có dữ liệu để so sánh nhu cầu giữa các nhóm giải pháp; chưa thể chọn nhóm cần tập trung."
    insights.append({"title": "Nhu cầu theo giải pháp", "text": solution_text})
    forecast = sorted(data.get("forecast", []), key=lambda row: row["date"])
    if forecast:
        first, last = forecast[0], forecast[-1]
        direction = "tăng" if last["predicted"] > first["predicted"] else ("giảm" if last["predicted"] < first["predicted"] else "đi ngang")
        forecast_text = (f"Dự báo cho {len(forecast)} tháng, từ {first['date'][:7]} đến {last['date'][:7]}, "
                         f"{direction} trong kỳ dự báo: từ {money(first['predicted'])} đến {money(last['predicted'])}. "
                         f"Phương pháp đang hiển thị: {first['trend']}. "
                         "Cần đối chiếu doanh thu WON thực tế; dải sai số chỉ tham khảo, chưa là khoảng tin cậy 95% đã kiểm định.")
    else:
        forecast_text = "Chưa đủ lịch sử để dự báo doanh thu (cần ít nhất 3 tháng). Không suy đoán xu hướng khi thiếu dữ liệu."
    insights.append({"title": "Xu hướng doanh thu", "text": forecast_text})
    sentiments = data.get("sentiment", [])
    interactions = sum(row["count"] for row in sentiments)
    negative = sum(row["count"] for row in sentiments if row["label"] == "NEGATIVE")
    high = sum(row["count"] for row in data.get("churn_risk", []) if row["level"] == "HIGH")
    insights.append({"title": "Cảm xúc và nguy cơ cần chăm sóc", "text": (
        f"Có {negative}/{interactions} lượt tương tác mang cảm xúc tiêu cực và {high} lượt được đánh dấu rủi ro HIGH. "
        "Các lượt có thể thuộc cùng một khách hàng. Nên đọc nội dung và kiểm tra việc chưa xử lý trước khi liên hệ; cảnh báo chưa chứng minh khách sẽ rời bỏ."
        if interactions else "Chưa có tương tác được phép phân tích để nhận xét cảm xúc hoặc rủi ro. Không xem thiếu dữ liệu là dấu hiệu khách hàng hài lòng."
    )})
    clusters = data.get("rfm_clusters", [])
    if clusters:
        largest = max(clusters, key=lambda row: row["count"])
        rfm_text = (f"Nhóm {largest['cluster']} có {largest['count']} khách, là một trong các nhóm lớn nhất. "
                    "Dùng nhóm này để chuẩn bị kế hoạch chăm sóc; RFM hiện dựa trên lần liên hệ, số tương tác và tổng chi tiêu với tâm tham chiếu cố định.")
    else:
        rfm_text = "Chưa có nhóm RFM để so sánh. Cần bổ sung lịch sử tương tác và chi tiêu trước khi thiết kế kế hoạch chăm sóc theo nhóm."
    insights.append({"title": "Phân nhóm chăm sóc", "text": rfm_text})
    features = data.get("xai", [])
    if features:
        top = max(features, key=lambda row: row["weight"])
        feature_text = (f"{top['feature']} có đóng góp tổng hợp lớn nhất trong công thức hiện tại ({top['weight']:.0%}). "
                        "Đây là phân rã điểm theo công thức, không phải bằng chứng nhân quả hay SHAP. Kiểm tra lại dữ liệu đầu vào trước khi quyết định.")
    else:
        feature_text = "Chưa có đóng góp đặc trưng để giải thích điểm. Chưa thể kết luận yếu tố nào ảnh hưởng nhiều nhất."
    insights.append({"title": "Giải thích điểm ưu tiên", "text": feature_text})
    return insights
