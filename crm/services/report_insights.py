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
        top = max(solutions, key=lambda row: row["expected_won"])
        solution_text = (f"{labels.get(top['solution'], top['solution'])} có giá trị cơ hội quy đổi lớn nhất, "
                         f"ở mức {money(top['expected_won'])} từ {top['count']} yêu cầu. Nên xác minh nhu cầu và giá trị hợp đồng của nhóm này. "
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
    sentiment_text = (
        f"Có {negative}/{interactions} lượt tương tác mang cảm xúc tiêu cực ({negative / interactions:.0%}). "
        "Nên đọc nội dung để xác minh vấn đề và mức độ ảnh hưởng trước khi phản hồi. Không xem nhãn cảm xúc là kết luận khách sẽ rời bỏ."
        if interactions else "Chưa có tương tác được phép phân tích. Không xem thiếu dữ liệu là dấu hiệu khách hàng hài lòng."
    )
    churn_total = sum(row["count"] for row in data.get("churn_risk", []))
    churn_text = (
        f"Có {high}/{churn_total} lượt tương tác được đánh dấu rủi ro HIGH. Các lượt có thể thuộc cùng một khách hàng. "
        "Ưu tiên kiểm tra phản hồi tiêu cực, thời gian chưa liên hệ và việc còn mở; chưa thể khẳng định khách sẽ rời bỏ."
        if churn_total else "Chưa có dữ liệu đánh giá rủi ro. Cần bổ sung lịch sử tương tác được phép phân tích trước khi xác định đối tượng cần chăm sóc."
    )
    alerts = data.get("anomaly_summary", [])
    alert_total = sum(row["count"] for row in alerts)
    high_alerts = sum(row["count"] for row in alerts if row["severity"] == "HIGH")
    anomaly_text = (
        f"Phát hiện {alert_total} cảnh báo, trong đó {high_alerts} cảnh báo mức HIGH. "
        "Kiểm tra lead bị bỏ quên và giao dịch lệch ngưỡng trước khi xử lý; cảnh báo không đồng nghĩa giao dịch gian lận."
        if alert_total else "Chưa ghi nhận cảnh báo bất thường trong dữ liệu đang phân tích. Điều này không bảo đảm mọi giao dịch hoặc quy trình đều không có rủi ro."
    )
    return [insights[0], insights[1],
            {"title": "Cảm xúc tương tác", "text": sentiment_text},
            {"title": "Rủi ro cần chăm sóc", "text": churn_text},
            insights[3], insights[2], insights[4],
            {"title": "Cảnh báo bất thường", "text": anomaly_text}]
