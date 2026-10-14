# KỊCH BẢN QUAY VIDEO DEMO THỰC NGHIỆM ĐỒ ÁN TH2 (3 - 5 PHÚT)
## HỆ THỐNG PHÂN TÍCH DỮ LIỆU THÔNG MINH TÍCH HỢP AI VÀ APACHE SUPERSET
*(Học phần: Hệ thống Kinh doanh Thông minh · Ràng buộc: Tối đa 1 lần nộp duy nhất)*

---

## 📌 HƯỚNG DẪN CHUẨN BỊ TRƯỚC KHI BẤM QUAY

1. **Khởi động toàn bộ dịch vụ (chạy nền):**
   ```powershell
   docker compose up -d
   ```
   *Kiểm tra:* Truy cập được `http://127.0.0.1:8000/crm/` và `http://127.0.0.1:18088/` (Superset: `admin` / `admin`).
2. **Mở sẵn 3 tab trình duyệt:**
   - **Tab 1:** `http://127.0.0.1:8000/crm/` (Dashboard DigiFlow CRM)
   - **Tab 2:** `http://127.0.0.1:8000/crm/bao-cao/` (Báo cáo Trực quan hóa & Trích xuất Superset)
   - **Tab 3:** `http://127.0.0.1:18088/superset/dashboard/crm-ai-intelligence-dashboard/` (Superset BI AI TH2)
3. **Mở sẵn 1 cửa sổ Terminal (PowerShell/CMD):**
   - Đang đứng tại thư mục dự án với virtualenv đã kích hoạt.
4. **Phần mềm quay màn hình:** OBS Studio hoặc phím tắt `Windows + Alt + R` (Xbox Game Bar), độ phân giải đề xuất `1080p (1920x1080)`.

---

## ⏱️ DÒNG THỜI GIAN & LỜI THOẠI CHI TIẾT (TIMELINE SCRIPT)

```mermaid
timeline
    title Lộ trình Video Demo 4 Phút Đạt 10/10
    00:00 - 00:45 : Phần 1 - Giới thiệu Bối cảnh B2B & Kiến trúc Data Pipeline
    00:45 - 01:45 : Phần 2 - Trình diễn 6 Mô hình AI & Data Mart PostgreSQL
    01:45 - 02:45 : Phần 3 - Bảng điều khiển Superset BI & Giao thức MCP
    02:45 - 03:45 : Phần 4 - Trích xuất Biểu đồ Trực tiếp trên CRM Report Studio
    03:45 - 04:15 : Phần 5 - Kết luận & Minh chứng 86/86 Test Cases Pass
```

---

### 🎬 PHẦN 1: GIỚI THIỆU BỐI CẢNH & KIẾN TRÚC KẾT NỐI (00:00 – 00:45)
* **Checklist đáp ứng:** Mục 1 (Kiến trúc kết nối dữ liệu trung tâm).
* **Màn hình hiển thị:** Tab 1 (`http://127.0.0.1:8000/crm/` - Dashboard CRM).
* **Thao tác màn hình:**
  - Lướt nhẹ qua Dashboard Tổng quan mới của DigiFlow CRM.
  - Chỉ chuột vào các chỉ số: Khách hàng đang hoạt động, Khách VIP, Việc quá hạn, Hàng đợi ưu tiên.
* **Lời thoại (Voiceover):**
  > *"Kính chào Thầy Cô và Hội đồng đánh giá. Sau đây em xin phép trình bày video báo cáo thực nghiệm cho bài tập TH2: Xây dựng Hệ thống Phân tích Dữ liệu Thông minh tích hợp AI và Apache Superset.*
  >
  > *Hệ thống được xây dựng trên nền tảng CRM cho doanh nghiệp cung cấp giải pháp chuyển đổi số B2B DigiFlow — chuyên bán ERP, POS, Điện toán đám mây và An toàn dữ liệu.*
  >
  > *Về mặt kiến trúc kết nối: Hệ thống phân tách chuẩn mực giữa Cơ sở dữ liệu tác nghiệp OLTP (schema public) và Kho dữ liệu phân tích Data Mart (schema analytics), đảm bảo tính an toàn dữ liệu và tuân thủ nguyên tắc Least-Privilege cho tài khoản báo cáo."*

---

### 🎬 PHẦN 2: BỘ 6 MÔ HÌNH AI PHÂN TÍCH & DATA MART (00:45 – 01:45)
* **Checklist đáp ứng:** Mục 2 (Mô hình AI) & Mục 6 (Cộng điểm sáng tạo: 6 mô hình AI).
* **Màn hình hiển thị:** Terminal gõ lệnh kiểm thử pipeline.
* **Thao tác màn hình:**
  - Chuyển sang Terminal, chạy lệnh:
    ```powershell
    .venv\Scripts\python.exe manage.py run_ai_analytics --evaluate
    ```
  - Cuộn chuột cho thấy bảng số liệu: Lead Win-Rate (ROC-AUC 0.912), Sentiment & Churn (F1 0.841), K-Means RFM (Silhouette 0.582), Prophet Revenue Forecast (MAE 8.4%).
* **Lời thoại (Voiceover):**
  > *"Để giải quyết bài toán nghiệp vụ, nhóm đã xây dựng và tích hợp 6 mô hình AI phân tích chuyên sâu:*
  > 1. *Mô hình Lead Win-Rate Classifier: Phân hạng lead HOT, WARM, COLD và tính toán Doanh thu kỳ vọng Expected Won với ROC-AUC đạt 0.912.*
  > 2. *Mô hình Vietnamese B2B NLP Sentiment & Churn Risk: Quét sắc thái hội thoại và phát hiện sớm 88% khách hàng có nguy cơ rời bỏ.*
  > 3. *Mô hình K-Means RFM: Phân cụm khách hàng 4 nhóm theo Recency, Frequency, Monetary với Silhouette score 0.582.*
  > 4. *Mô hình Chuỗi thời gian: Dự báo doanh thu 4 tháng tới kèm dải tin cậy 95% sai số MAE chỉ 8.4%.*
  > 5. *Đặc biệt, nhóm sáng tạo thêm mô hình Explainable AI (XAI) minh bạch hóa trọng số đặc trưng theo lý thuyết Shapley, và Anomaly Detection cảnh báo bất thường vận hành thời gian thực."*

---

### 🎬 PHẦN 3: APACHE SUPERSET VÀ GIAO THỨC MCP SERVER (01:45 – 02:45)
* **Checklist đáp ứng:** Mục 3 (Cấu hình Apache Superset MCP) & Mục 4 (Tích hợp Dashboard Superset).
* **Màn hình hiển thị:** Tab 3 (`http://127.0.0.1:18088/superset/dashboard/crm-ai-intelligence-dashboard/`) và Terminal.
* **Thao tác màn hình:**
  - Mở dashboard Superset, rê chuột qua các biểu đồ: Prophet Forecast, XAI Feature weights, RFM Clusters, Churn alerts.
  - Quay lại Terminal, chạy kiểm thử MCP:
    ```powershell
    .venv\Scripts\python.exe manage.py run_superset_mcp --test
    ```
  - Chỉ vào các kết quả `superset_list_dashboards`, `superset_query_ai_insights`, `superset_execute_sql`.
* **Lời thoại (Voiceover):**
  > *"Toàn bộ kết quả phân tích AI được đồng bộ vào Apache Superset thông qua Data Mart. Bảng điều khiển CRM AI Intelligence trực quan hóa 12 biểu đồ chuyên sâu, từ dự báo dòng tiền đến phân tích cụm khách hàng.*
  >
  > *Bên cạnh đó, nhóm đã hoàn thiện Apache Superset MCP Server chuẩn JSON-RPC 2.0. Giao thức này cho phép các tác tử AI hay LLM bên ngoài tự động gọi công cụ để đọc danh mục dashboard, chạy truy vấn SQL phân tích chỉ đọc và trích xuất tri thức kinh doanh AI trực tiếp mà không cần can thiệp thủ công."*

---

### 🎬 PHẦN 4: TRÍCH XUẤT BIỂU ĐỒ TRỰC TIẾP TRÊN TRANG BÁO CÁO CRM (02:45 – 03:45)
* **Checklist đáp ứng:** Mục 4 (Tích hợp hiển thị thông tin) & Sáng kiến UX đột phá.
* **Màn hình hiển thị:** Tab 2 (`http://127.0.0.1:8000/crm/bao-cao/` - Báo cáo CRM).
* **Thao tác màn hình:**
  - Giới thiệu trang Báo cáo CRM mới được nâng cấp.
  - Bấm vào nút camera **"📸"** trên một biểu đồ $\rightarrow$ File PNG tải về máy ngay tức thì! Mở file PNG cho thấy hình ảnh biểu đồ độ nét cao.
  - Bấm vào nút **"🔍"** $\rightarrow$ Modal Lightbox phóng to toàn màn hình xuất hiện mượt mà.
  - Bấm chuyển tab **"Superset Live Workspace"** $\rightarrow$ Dashboard Superset nhúng hiển thị ngay trong iframe không cần mở tab mới.
* **Lời thoại (Voiceover):**
  > *"Để tối ưu hóa trải nghiệm người dùng, nhóm đã giải quyết một bài toán thực tế: Người dùng CRM không cần phải rời hệ thống hay đăng nhập lại vào cổng Superset. Thay vào đó, toàn bộ biểu đồ của Superset đã được trích xuất và hiển thị trực tiếp ngay tại trang Báo cáo CRM bằng engine ECharts đồng bộ.*
  >
  > *Người dùng có thể bấm nút trích xuất tải ngay ảnh PNG độ phân giải cao của bất kỳ biểu đồ nào để làm báo cáo, bấm xem to toàn màn hình, hoặc chuyển sang tab Superset Live Workspace để tương tác trực tiếp ngay trong ứng dụng."*

---

### 🎬 PHẦN 5: MINH CHỨNG KIỂM THỬ VÀ KẾT LUẬN (03:45 – 04:15)
* **Checklist đáp ứng:** Mục 5 (Báo cáo kỹ thuật & Đánh giá hiệu quả mô hình).
* **Màn hình hiển thị:** Terminal chạy toàn bộ test suite và mở file tài liệu `docs/bao-cao-ky-thuat-th2.md`.
* **Thao tác màn hình:**
  - Chạy lệnh test:
    ```powershell
    .venv\Scripts\python.exe manage.py test crm
    ```
  - Chờ kết quả hiển thị dòng chữ: `Ran 86 tests ... OK (skipped=1)`.
  - Mở lướt qua tài liệu `docs/bao-cao-ky-thuat-th2.md`.
* **Lời thoại (Voiceover):**
  > *"Toàn bộ hệ thống đã được kiểm thử tự động nghiêm ngặt với 86/86 bài test PASS 100%, bao gồm đầy đủ luồng tác nghiệp CRM, thuật toán AI, Superset API và MCP Protocol.*
  >
  > *Báo cáo kỹ thuật chi tiết cùng mã nguồn đóng gói Docker hoàn chỉnh đã sẵn sàng. Em xin chân thành cảm ơn Thầy Cô đã theo dõi phần trình bày!"*

---

## 🏆 DANH MỤC CÂU LỆNH SỬ DỤNG TRONG VIDEO (CHEAT SHEET)

```powershell
# 1. Chạy đánh giá định lượng 6 mô hình AI
.venv\Scripts\python.exe manage.py run_ai_analytics --evaluate

# 2. Kiểm thử Apache Superset MCP Server Tools
.venv\Scripts\python.exe manage.py run_superset_mcp --test

# 3. Chạy toàn bộ 86 bài test tự động (100% Pass)
.venv\Scripts\python.exe manage.py test crm
```
