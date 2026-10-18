"""Script to generate a high-resolution, professional architecture diagram for the CRM-AI-Superset system."""

from pathlib import Path
from playwright.sync_api import sync_playwright

HTML_CONTENT = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Kiến trúc Luồng dữ liệu CRM - AI - Apache Superset MCP</title>
<style>
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  body {
    background: #0f172a;
    color: #f8fafc;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 30px;
  }
  .container {
    width: 1480px;
    background: #1e293b;
    border-radius: 20px;
    border: 1px solid #334155;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    padding: 36px 42px;
    position: relative;
  }
  .header {
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 1px solid #334155;
    padding-bottom: 20px;
  }
  .header h1 {
    font-size: 26px;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  .header p {
    font-size: 14px;
    color: #94a3b8;
  }
  
  .diagram-grid {
    display: grid;
    grid-template-columns: 310px 60px 330px 60px 320px 60px 240px;
    align-items: center;
  }

  /* Columns & Cards */
  .col {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    position: relative;
    transition: all 0.2s;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  .card-title {
    font-size: 15px;
    font-weight: 700;
  }
  .card-desc {
    font-size: 12.5px;
    color: #94a3b8;
    line-height: 1.45;
  }
  .card-tag {
    display: inline-block;
    font-size: 10.5px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 9999px;
    margin-top: 8px;
    text-transform: uppercase;
  }

  /* Card Color Themes */
  .card-blue {
    border-left: 4px solid #38bdf8;
  }
  .card-blue .card-title { color: #38bdf8; }
  .card-blue .card-tag { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }

  .card-purple {
    border-left: 4px solid #a855f7;
  }
  .card-purple .card-title { color: #c084fc; }
  .card-purple .card-tag { background: rgba(168, 85, 247, 0.15); color: #d8b4fe; }

  .card-emerald {
    border-left: 4px solid #10b981;
  }
  .card-emerald .card-title { color: #34d399; }
  .card-emerald .card-tag { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }

  .card-amber {
    border-left: 4px solid #f59e0b;
  }
  .card-amber .card-title { color: #fbbf24; }
  .card-amber .card-tag { background: rgba(245, 158, 11, 0.15); color: #fde68a; }

  .card-cyan {
    border-left: 4px solid #06b6d4;
  }
  .card-cyan .card-title { color: #22d3ee; }
  .card-cyan .card-tag { background: rgba(6, 182, 212, 0.15); color: #67e8f9; }

  .card-rose {
    border-left: 4px solid #f43f5e;
  }
  .card-rose .card-title { color: #fb7185; }
  .card-rose .card-tag { background: rgba(244, 63, 94, 0.15); color: #fecdd3; }

  /* Arrows */
  .arrow-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    height: 100%;
  }
  .arrow-svg {
    width: 50px;
    height: 40px;
  }
  .arrow-label {
    font-size: 11px;
    color: #64748b;
    font-weight: 500;
    text-align: center;
    margin-top: -2px;
  }

  /* Zone Boxes */
  .zone-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
    padding-left: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .zone-blue { color: #38bdf8; }
  .zone-emerald { color: #34d399; }
  .zone-purple { color: #c084fc; }
  .zone-amber { color: #fbbf24; }

  /* Security & Protocol Badges */
  .footer-legend {
    margin-top: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 12px 24px;
    font-size: 12.5px;
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .badge-icon {
    font-size: 16px;
  }
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>
      <span>🏗️</span>
      KIẾN TRÚC KẾT NỐI VÀ LUỒNG DỮ LIỆU CRM B2B - AI - APACHE SUPERSET
    </h1>
    <p>Quy trình xử lý dữ liệu chuẩn hóa: Tác nghiệp OLTP → Lọc Consent & Phân tích AI → Data Mart OLAP → Trực quan hóa qua Superset MCP</p>
  </div>

  <div class="diagram-grid">
    <!-- CỘT 1: CRM TÁC NGHIỆP -->
    <div class="col">
      <div class="zone-title zone-blue">
        <span>🌐</span> 1. CRM Tác nghiệp (OLTP)
      </div>

      <div class="card card-blue">
        <div class="card-header">
          <span class="badge-icon">📝</span>
          <div class="card-title">Form Tư vấn & Portal</div>
        </div>
        <div class="card-desc">Khách hàng B2B gửi nhu cầu giải pháp chuyển đổi số (Kho, POS, CRM, ERP).</div>
        <div class="card-tag">Wagtail CMS & Django</div>
      </div>

      <div class="card card-blue">
        <div class="card-header">
          <span class="badge-icon">👥</span>
          <div class="card-title">Tác nghiệp Kinh doanh</div>
        </div>
        <div class="card-desc">Nhân viên quản lý Lead, ghi nhận lịch sử tương tác, tạo CareTask & Email nháp.</div>
        <div class="card-tag">Human-In-The-Loop</div>
      </div>

      <div class="card card-cyan">
        <div class="card-header">
          <span class="badge-icon">💾</span>
          <div class="card-title">PostgreSQL (public)</div>
        </div>
        <div class="card-desc">Lưu Customer, LeadRequest, Interaction, CareTask, SalesRecord.</div>
        <div class="card-tag">CSDL Tác nghiệp OLTP</div>
      </div>
    </div>

    <!-- MŨI TÊN 1 -> 2 -->
    <div class="arrow-container">
      <svg class="arrow-svg" viewBox="0 0 50 40">
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#38bdf8"/>
            <stop offset="100%" stop-color="#34d399"/>
          </linearGradient>
          <marker id="arrowhead1" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#34d399" />
          </marker>
        </defs>
        <line x1="2" y1="20" x2="40" y2="20" stroke="url(#grad1)" stroke-width="3" marker-end="url(#arrowhead1)"/>
      </svg>
      <div class="arrow-label">Trích xuất</div>
    </div>

    <!-- CỘT 2: PIPELINE & BỘ MÁY AI -->
    <div class="col">
      <div class="zone-title zone-emerald">
        <span>⚙️</span> 2. Pipeline & Bộ máy AI
      </div>

      <div class="card card-emerald">
        <div class="card-header">
          <span class="badge-icon">🛡️</span>
          <div class="card-title">AnalyticsPipeline</div>
        </div>
        <div class="card-desc"><strong>Lọc Quyền riêng tư (Consent Engine):</strong> Chỉ trích xuất hồ sơ có <code>consent_for_ai=True</code>. Loại bỏ PII.</div>
        <div class="card-tag">Bảo vệ dữ liệu B2B</div>
      </div>

      <div class="card card-purple">
        <div class="card-header">
          <span class="badge-icon">✨</span>
          <div class="card-title">Google Gemini LLM</div>
        </div>
        <div class="card-desc">Phân tích hồ sơ định tính, chấm điểm, nhận định nhu cầu. Có <strong>Rules Fallback</strong> tự động.</div>
        <div class="card-tag">JSON Output & Checklist</div>
      </div>

      <div class="card card-emerald">
        <div class="card-header">
          <span class="badge-icon">🧠</span>
          <div class="card-title">Bộ máy Phân tích AI</div>
        </div>
        <div class="card-desc">• <strong>Sentiment/Churn:</strong> Lexicon tiếng Việt<br/>• <strong>Scoring:</strong> Sigmoid đa biến<br/>• <strong>Dự báo:</strong> Baseline Naive & Trend<br/>• <strong>Bất thường:</strong> Z-Score & Ngưỡng</div>
        <div class="card-tag">Tính toán định lượng</div>
      </div>
    </div>

    <!-- MŨI TÊN 2 -> 3 -->
    <div class="arrow-container">
      <svg class="arrow-svg" viewBox="0 0 50 40">
        <defs>
          <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#34d399"/>
            <stop offset="100%" stop-color="#fbbf24"/>
          </linearGradient>
          <marker id="arrowhead2" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#fbbf24" />
          </marker>
        </defs>
        <line x1="2" y1="20" x2="40" y2="20" stroke="url(#grad2)" stroke-width="3" marker-end="url(#arrowhead2)"/>
      </svg>
      <div class="arrow-label">Atomic Trans</div>
    </div>

    <!-- CỘT 3: DATA MART PHÂN TÍCH -->
    <div class="col">
      <div class="zone-title zone-amber">
        <span>📊</span> 3. Data Mart (OLAP)
      </div>

      <div class="card card-amber">
        <div class="card-header">
          <span class="badge-icon">🗄️</span>
          <div class="card-title">Schema `analytics`</div>
        </div>
        <div class="card-desc">Kho lưu trữ kết quả phân tích trong PostgreSQL:
          <ul style="padding-left: 16px; margin-top: 4px; font-size: 11.5px; color: #cbd5e1;">
            <li><code>ai_lead_predictions</code></li>
            <li><code>ai_sentiment_churn</code></li>
            <li><code>ai_customer_rfm_segments</code></li>
            <li><code>ai_revenue_forecast</code></li>
            <li><code>ai_anomaly_alerts</code></li>
            <li><code>ai_explainability_summary</code></li>
          </ul>
        </div>
        <div class="card-tag">6 Bảng AI + 4 View OLAP</div>
      </div>

      <div class="card card-rose">
        <div class="card-header">
          <span class="badge-icon">🔒</span>
          <div class="card-title">Role `superset_ro`</div>
        </div>
        <div class="card-desc">Tài khoản kết nối riêng biệt: <strong>Chỉ đọc (Read-only)</strong>, Timeout bảo vệ, cấm ghi sửa bảng CRM.</div>
        <div class="card-tag">Bảo mật cấp CSDL</div>
      </div>
    </div>

    <!-- MŨI TÊN 3 -> 4 -->
    <div class="arrow-container">
      <svg class="arrow-svg" viewBox="0 0 50 40">
        <defs>
          <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#fbbf24"/>
            <stop offset="100%" stop-color="#c084fc"/>
          </linearGradient>
          <marker id="arrowhead3" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#c084fc" />
          </marker>
        </defs>
        <line x1="2" y1="20" x2="40" y2="20" stroke="url(#grad3)" stroke-width="3" marker-end="url(#arrowhead3)"/>
      </svg>
      <div class="arrow-label">MCP / REST</div>
    </div>

    <!-- CỘT 4: SUPERSET BI & MCP -->
    <div class="col">
      <div class="zone-title zone-purple">
        <span>📈</span> 4. Apache Superset
      </div>

      <div class="card card-purple">
        <div class="card-header">
          <span class="badge-icon">🤖</span>
          <div class="card-title">Superset MCP Server</div>
        </div>
        <div class="card-desc">Giao thức MCP stdio cho AI Agent: 7 công cụ khám phá, chạy SQL và <strong>Authoring API</strong> tự động tạo biểu đồ.</div>
        <div class="card-tag">Model Context Protocol</div>
      </div>

      <div class="card card-purple">
        <div class="card-header">
          <span class="badge-icon">📊</span>
          <div class="card-title">Dashboard Superset</div>
        </div>
        <div class="card-desc">10 Dataset, 12 Chart trực quan hóa Lead, RFM, Churn, Dự báo doanh thu.</div>
        <div class="card-tag">BI Intelligence</div>
      </div>

      <div class="card card-blue">
        <div class="card-header">
          <span class="badge-icon">🔗</span>
          <div class="card-title">Embedded SDK</div>
        </div>
        <div class="card-desc">Nhúng trực tiếp vào CRM qua <strong>Guest Token (5p)</strong>, bảo vệ CSRF và <code>frame-ancestors</code>.</div>
        <div class="card-tag">Giao diện Báo cáo CRM</div>
      </div>
    </div>
  </div>

  <div class="footer-legend">
    <div class="legend-item">
      <div class="legend-dot" style="background: #38bdf8;"></div>
      <span><strong>Tác nghiệp:</strong> Django 5 + Wagtail 7 (OLTP)</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #10b981;"></div>
      <span><strong>Quyền riêng tư:</strong> Consent Filter bắt buộc</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #c084fc;"></div>
      <span><strong>Trí tuệ nhân tạo:</strong> Gemini 2.5 Flash + Fallback Rules</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #f59e0b;"></div>
      <span><strong>Lưu trữ phân tích:</strong> PostgreSQL 16 (Schema `analytics`)</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #fb7185;"></div>
      <span><strong>Bảo mật:</strong> Role Read-Only `superset_ro` + Guest Token</span>
    </div>
  </div>
</div>

</body>
</html>
"""

def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path("docs/images")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "kientruc-luong-dulieu-crm-ai-superset.png"

    print("Khoi chay Playwright de render so do...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1540, "height": 840},
            device_scale_factor=2  # High resolution (2x DPI)
        )
        page.set_content(HTML_CONTENT)
        page.wait_for_timeout(500)
        
        container = page.locator(".container")
        container.screenshot(path=str(out_file))
        browser.close()

    print(f"Rendered successfully: {out_file} ({out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
