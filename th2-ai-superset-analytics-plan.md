# Kế hoạch phát triển: Hệ thống Phân tích Dữ liệu Thông minh tích hợp AI & Apache Superset (TH2)

## 1. Mục tiêu
Thiết kế và triển khai module phân tích dữ liệu thông minh cho hệ thống CRM B2B (DigiFlow), kết hợp bộ đa mô hình AI (Chấm điểm Lead, Phân tích Cảm xúc, Phân khúc K-Means, Dự báo Doanh thu) và trực quan hóa chuyên sâu trên Apache Superset thông qua Apache Superset MCP Server.

---

## 2. Danh sách công việc theo 6 tiêu chí Checklist

### Mục 1: Kiến trúc kết nối dữ liệu (Data Pipeline & Analytics Mart)
- [ ] Task 1.1: Thiết kế schema `analytics` trên PostgreSQL 16 (Star Schema: `dim_customers`, `dim_solutions`, `fact_lead_funnel`, `fact_interactions`, `fact_ai_predictions`).
- [ ] Task 1.2: Xây dựng script ETL trích xuất, làm sạch và nạp dữ liệu từ các bảng CRM sang `analytics` (`crm/analytics/etl_pipeline.py`).
  → *Nghiệm thu*: Chạy command ETL thành công, dữ liệu sẵn sàng cho truy vấn phân tích.

### Mục 2: Triển khai các mô hình AI phân tích dữ liệu
- [ ] Task 2.1: Mô hình Chấm điểm Lead & Xác suất Chốt đơn (Random Forest / XGBoost Classifier).
- [ ] Task 2.2: Mô hình Phân tích Cảm xúc & Cảnh báo Churn Risk từ lịch sử trao đổi/chat (NLP / VADER + Gemini).
- [ ] Task 2.3: Mô hình Phân khúc Khách hàng Đa chiều (RFM Metrics + K-Means Clustering).
- [ ] Task 2.4: Mô hình Dự báo Doanh thu theo chuỗi thời gian (Time-Series Prophet / ARIMA).
- [ ] Task 2.5: Đóng gói AI Service Pipeline (`crm/analytics/ai_engine.py`) tự động ghi kết quả vào Data Mart.
  → *Nghiệm thu*: Bảng `fact_ai_predictions` đầy đủ metrics, các chỉ số đánh giá kỹ thuật (ROC-AUC > 0.82, Silhouette > 0.55).

### Mục 3: Cấu hình Apache Superset & Superset MCP Server
- [ ] Task 3.1: Thêm service `superset` vào `docker-compose.yml`, script khởi tạo tự động (admin, db upgrade, init).
- [ ] Task 3.2: Cấu hình kết nối Datasource từ Superset tới PostgreSQL `crm-db` (`postgresql://postgres:postgres@crm-db:5432/crm_db`).
- [ ] Task 3.3: Cấu hình Superset MCP Server để tương tác, truy vấn SQL Lab và sinh chart bằng AI Agent.
  → *Nghiệm thu*: Superset Web UI hoạt động tại `http://localhost:8088`, kết nối database thành công, MCP tools phản hồi tốt.

### Mục 4: Tích hợp kết quả phân tích AI vào các Dashboard Superset
- [ ] Task 4.1: Dashboard 1 - Executive Overview & Dự báo Doanh số (KPI Cards, Phễu chuyển đổi Funnel, Biểu đồ Prophet).
- [ ] Task 4.2: Dashboard 2 - Ma trận Tiềm năng Lead & Điểm AI (Scatter Plot cơ hội, Grouped Bar theo 4 giải pháp, Top Priority Table).
- [ ] Task 4.3: Dashboard 3 - Cảm xúc Khách hàng & Cảnh báo Churn Radar (Donut Chart, Trendline cảm xúc, Heatmap rủi ro).
- [ ] Task 4.4: Dashboard 4 - Phân khúc Khách hàng RFM & K-Means Clusters (Cluster Scatter, Treemap tỷ trọng doanh thu).
  → *Nghiệm thu*: 4 Dashboards hiển thị trực quan, filter tương tác thời gian thực mượt mà.

### Mục 5: Đề xuất phương pháp AI sáng tạo (Bonus Points)
- [ ] Task 5.1: Explainable AI (XAI) với SHAP Values (giải thích tại sao AI chấm điểm khách hàng, hiển thị Waterfall Chart).
- [ ] Task 5.2: ChatBI / Natural Language to SQL qua Superset MCP (Hỏi bot bằng tiếng Việt → tự động sinh chart và câu trả lời).
- [ ] Task 5.3: Thuật toán Phát hiện Bất thường (Isolation Forest Anomaly Detection) cảnh báo lead bị ngâm hoặc doanh số sụt giảm bất thường.
- [ ] Task 5.4: LLM Executive Insights Generator tự động sinh báo cáo tuần cho ban giám đốc.
  → *Nghiệm thu*: Các tính năng sáng tạo hoạt động có minh họa cụ thể trên dashboard và code.

### Mục 6: Viết báo cáo kỹ thuật & Đánh giá hiệu quả mô hình
- [ ] Task 6.1: Soạn thảo Báo cáo Kỹ thuật (Technical Report) 6 chương chuẩn khoa học: Kiến trúc, Dữ liệu, Mô hình toán, Superset, Đánh giá thực nghiệm, Kết luận.
- [ ] Task 6.2: Kiểm thử hồi quy hệ thống (`python manage.py test` 76/76 PASS) và xác nhận luồng End-to-End.
  → *Nghiệm thu*: File báo cáo hoàn chỉnh (`docs/bao-cao-ky-thuat-th2.md` hoặc PDF), repository sạch sẽ, tài liệu hướng dẫn chạy 1-click.

---

## 3. Tiêu chí hoàn thành (Done When)
- [ ] Toàn bộ 6 mục trong checklist đề bài TH2 được triển khai và kiểm chứng đầy đủ.
- [ ] Apache Superset kết nối trực tiếp với PostgreSQL, hiển thị 4 Dashboard với kết quả thực tế từ các mô hình AI.
- [ ] Báo cáo kỹ thuật chi tiết với công thức toán, chỉ số đo lường (Confusion Matrix, Precision/Recall, RMSE/MAE).
