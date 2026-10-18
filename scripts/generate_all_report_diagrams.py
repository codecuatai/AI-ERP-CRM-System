"""Generate all missing high-resolution architecture and evaluation diagrams for the technical report."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COMMON_CSS = """
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
    padding: 24px;
  }
  .container {
    width: 1440px;
    background: #1e293b;
    border-radius: 20px;
    border: 1px solid #334155;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    padding: 32px 36px;
    position: relative;
  }
  .header {
    text-align: center;
    margin-bottom: 26px;
    border-bottom: 1px solid #334155;
    padding-bottom: 16px;
  }
  .header h1 {
    font-size: 25px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  .header p {
    font-size: 13.5px;
    color: #94a3b8;
  }
  .card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
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
  .footer-legend {
    margin-top: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 12px;
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .legend-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }
"""

# 1. DIAGRAM: SECURITY, CONSENT & AUTHORIZATION (Mục 3)
HTML_SECURITY = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
  .header h1 {{ color: #38bdf8; }}
  .sec-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }}
  .step-box {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    position: relative;
  }}
  .step-num {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 12px;
  }}
  .step-title {{
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .step-content {{
    font-size: 12.5px;
    color: #94a3b8;
    line-height: 1.5;
    flex-grow: 1;
  }}
  .step-content ul {{
    padding-left: 16px;
    margin-top: 8px;
  }}
  .step-content li {{
    margin-bottom: 4px;
  }}
  .step-badge {{
    margin-top: 14px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    text-align: center;
  }}
  
  /* Themes */
  .theme-emerald {{ border-top: 4px solid #10b981; }}
  .theme-emerald .step-num {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
  .theme-emerald .step-title {{ color: #34d399; }}
  .theme-emerald .step-badge {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }}

  .theme-blue {{ border-top: 4px solid #38bdf8; }}
  .theme-blue .step-num {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; }}
  .theme-blue .step-title {{ color: #38bdf8; }}
  .theme-blue .step-badge {{ background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }}

  .theme-rose {{ border-top: 4px solid #f43f5e; }}
  .theme-rose .step-num {{ background: rgba(244, 63, 94, 0.2); color: #fb7185; }}
  .theme-rose .step-title {{ color: #fb7185; }}
  .theme-rose .step-badge {{ background: rgba(244, 63, 94, 0.15); color: #fecdd3; }}

  .theme-purple {{ border-top: 4px solid #a855f7; }}
  .theme-purple .step-num {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; }}
  .theme-purple .step-title {{ color: #c084fc; }}
  .theme-purple .step-badge {{ background: rgba(168, 85, 247, 0.15); color: #d8b4fe; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><span>🛡️</span> KIẾN TRÚC BẢO MẬT DỮ LIỆU, CONSENT & PHÂN QUYỀN TRUY CẬP (MỤC 3)</h1>
    <p>Quy trình bảo vệ quyền riêng tư 4 tầng: Từ biểu mẫu công khai đến phân quyền cơ sở dữ liệu và nhúng an toàn</p>
  </div>

  <div class="sec-grid">
    <!-- TẦNG 1 -->
    <div class="step-box theme-emerald">
      <div class="step-num">1</div>
      <div class="step-title"><span>📝</span> Consent Engine</div>
      <div class="step-content">
        Kiểm soát quyền riêng tư tại nguồn:
        <ul>
          <li>Tách bạch <strong>Đồng ý tiếp nhận</strong> và <strong>Đồng ý phân tích AI</strong>.</li>
          <li>Migration <code>0009</code>: Cột <code>consent_for_ai</code> cho từng bản ghi tương tác.</li>
          <li>Loại bỏ PII: Ẩn Tên, Email, SĐT trước khi gửi ngữ cảnh vào Prompt Gemini.</li>
          <li>Hồ sơ không đồng ý: Khóa phân tích AI an toàn, xử lý thủ công.</li>
        </ul>
      </div>
      <div class="step-badge">Tuân thủ Quyền Riêng Tư B2B</div>
    </div>

    <!-- TẦNG 2 -->
    <div class="step-box theme-blue">
      <div class="step-num">2</div>
      <div class="step-title"><span>🔑</span> Follow-up Token</div>
      <div class="step-content">
        Bảo vệ form tương tác ngoài:
        <ul>
          <li><strong>SHA-256 Hash Token:</strong> Khóa bí mật chỉ lưu hash trong database.</li>
          <li>Thời hạn giới hạn: Hết hạn sau 7 ngày hoặc thu hồi chủ động.</li>
          <li>Sử dụng một lần: Tự động vô hiệu sau khi khách phản hồi.</li>
          <li>Chính sách <code>strict-origin</code>: Bảo vệ CSRF và ngăn rò rỉ token qua Referer header.</li>
        </ul>
      </div>
      <div class="step-badge">Mã Hóa Một Chiều SHA-256</div>
    </div>

    <!-- TẦNG 3 -->
    <div class="step-box theme-rose">
      <div class="step-num">3</div>
      <div class="step-title"><span>🔒</span> CSDL Role `superset_ro`</div>
      <div class="step-content">
        Cô lập truy cập cơ sở dữ liệu:
        <ul>
          <li>Tài khoản riêng: Role chỉ đọc <code>superset_ro</code>.</li>
          <li>Chỉ SELECT trên schema <code>analytics</code>, từ chối toàn bộ <code>public.crm_*</code>.</li>
          <li>Ràng buộc giao dịch: <code>SET TRANSACTION READ ONLY</code>.</li>
          <li>Giới hạn thời gian truy vấn: <code>statement_timeout = 5s</code>.</li>
        </ul>
      </div>
      <div class="step-badge">Read-Only SQL Isolation</div>
    </div>

    <!-- TẦNG 4 -->
    <div class="step-box theme-purple">
      <div class="step-num">4</div>
      <div class="step-title"><span>🎟️</span> Guest Token & SDK</div>
      <div class="step-content">
        Nhúng Dashboard Superset vào CRM:
        <ul>
          <li>Endpoint <code>/crm/bao-cao/superset-session/</code> kiểm tra quyền <code>crm.access_crm</code>.</li>
          <li>Cấp <strong>Guest Token 5 phút</strong>: SDK tự động làm mới khi hết hạn.</li>
          <li>Trình duyệt không lưu cookie admin Superset, không lộ mật khẩu.</li>
          <li>Chính sách <code>frame-ancestors</code>: Chỉ cho phép nguồn gốc CRM nhúng iframe.</li>
        </ul>
      </div>
      <div class="step-badge">Superset Embedded Security</div>
    </div>
  </div>

  <div class="footer-legend">
    <div class="legend-item">
      <div class="legend-dot" style="background: #10b981;"></div>
      <span><strong>Consent Gate:</strong> Chặn trích xuất dữ liệu chưa được cấp phép</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #38bdf8;"></div>
      <span><strong>Token An Toàn:</strong> Chống Replay Attack & Rò rỉ Referer</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #fb7185;"></div>
      <span><strong>CSDL Cách Ly:</strong> Superset không có quyền ghi dữ liệu CRM</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #c084fc;"></div>
      <span><strong>Guest Token:</strong> Nhúng an toàn không chia sẻ tài khoản quản trị</span>
    </div>
  </div>
</div>
</body>
</html>
"""

# 2. DIAGRAM: APACHE SUPERSET MCP ARCHITECTURE (Mục 4)
HTML_MCP = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
  .header h1 {{ color: #c084fc; }}
  .mcp-grid {{
    display: grid;
    grid-template-columns: 320px 70px 480px 70px 380px;
    align-items: center;
  }}
  .tool-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
  }}
  .tool-item {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .tool-name {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px;
    color: #38bdf8;
    font-weight: 600;
  }}
  .tool-badge {{
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
  }}
  .tb-read {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
  .tb-write {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; }}
  .tb-exec {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; }}

  .arrow-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    gap: 4px;
  }}
  .arrow-line {{
    width: 45px;
    height: 2px;
    background: #475569;
    position: relative;
  }}
  .arrow-line::after {{
    content: '';
    position: absolute;
    right: 0;
    top: -4px;
    width: 0;
    height: 0;
    border-left: 8px solid #475569;
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><span>🤖</span> KIẾN TRÚC MÁY CHỦ APACHE SUPERSET MODEL CONTEXT PROTOCOL (MCP)</h1>
    <p>Cơ chế giao tiếp chuẩn stdio cho phép AI Agent tương tác, khám phá dữ liệu và tự động sinh biểu đồ (Authoring API)</p>
  </div>

  <div class="mcp-grid">
    <!-- KHỐI 1: CLIENT AGENT -->
    <div class="col" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="card" style="border-left: 4px solid #38bdf8;">
        <div class="card-header">
          <span style="font-size: 18px;">🧠</span>
          <div class="card-title" style="color: #38bdf8;">AI Agent & LLM</div>
        </div>
        <div class="card-desc">Tác nhân trí tuệ nhân tạo (Claude, Gemini, Antigravity) cần truy vấn dữ liệu kinh doanh hoặc tự động tạo dashboard theo lệnh tự nhiên.</div>
        <div class="card-tag" style="background: rgba(56, 189, 248, 0.15); color: #7dd3fc;">MCP Host Client</div>
      </div>

      <div class="card" style="border-left: 4px solid #10b981;">
        <div class="card-header">
          <span style="font-size: 18px;">⌨️</span>
          <div class="card-title" style="color: #34d399;">Giao Thức stdio</div>
        </div>
        <div class="card-desc">Giao thức JSON-RPC qua chuẩn đầu vào/đầu ra (stdio) của Python: hỗ trợ <code>initialize</code>, <code>ping</code>, <code>tools/list</code>, <code>tools/call</code>.</div>
        <div class="card-tag" style="background: rgba(16, 185, 129, 0.15); color: #6ee7b7;">Chuẩn Anthropic MCP</div>
      </div>
    </div>

    <!-- MŨI TÊN 1 -> 2 -->
    <div class="arrow-box">
      <span>JSON-RPC</span>
      <div class="arrow-line"></div>
      <span>stdio</span>
    </div>

    <!-- KHỐI 2: MCP SERVER & 7 TOOLS -->
    <div class="card" style="border-top: 4px solid #a855f7; padding: 20px;">
      <div class="card-header" style="justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 20px;">⚙️</span>
          <div class="card-title" style="color: #c084fc; font-size: 16px;">SupersetMCPServer (mcp_server.py)</div>
        </div>
        <span style="font-size: 11px; color: #a855f7; font-weight: 700;">7 TOOLS ĐƯỢC ĐĂNG KÝ</span>
      </div>

      <div class="tool-list">
        <div class="tool-item">
          <div>
            <div class="tool-name">superset_list_dashboards</div>
            <div style="font-size: 11px; color: #94a3b8;">Liệt kê danh sách dashboard, slug và trạng thái xuất bản</div>
          </div>
          <span class="tool-badge tb-read">Read</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_list_datasets</div>
            <div style="font-size: 11px; color: #94a3b8;">Khám phá danh sách bảng và metadata cột trong schema analytics</div>
          </div>
          <span class="tool-badge tb-read">Read</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_query_ai_insights</div>
            <div style="font-size: 11px; color: #94a3b8;">Rút trích các chỉ số KPI, phân khúc HOT/WARM, dự báo tổng hợp</div>
          </div>
          <span class="tool-badge tb-read">Read</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_execute_sql</div>
            <div style="font-size: 11px; color: #94a3b8;">Chạy SELECT an toàn trên schema analytics qua role superset_ro</div>
          </div>
          <span class="tool-badge tb-exec">SQL Sec</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_create_chart</div>
            <div style="font-size: 11px; color: #94a3b8;">Tạo biểu đồ mới (Pie, Bar, Line, Table) kèm xác thực confirm=True</div>
          </div>
          <span class="tool-badge tb-write">Authoring</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_create_dashboard</div>
            <div style="font-size: 11px; color: #94a3b8;">Tạo Dashboard nháp và liên kết các chart vừa sinh (Idempotent)</div>
          </div>
          <span class="tool-badge tb-write">Authoring</span>
        </div>

        <div class="tool-item">
          <div>
            <div class="tool-name">superset_trigger_pipeline</div>
            <div style="font-size: 11px; color: #94a3b8;">Kích hoạt pipeline tính toán lại toàn bộ kết quả phân tích AI</div>
          </div>
          <span class="tool-badge tb-exec">Pipeline</span>
        </div>
      </div>
    </div>

    <!-- MŨI TÊN 2 -> 3 -->
    <div class="arrow-box">
      <span>REST / SQL</span>
      <div class="arrow-line"></div>
      <span>API v1</span>
    </div>

    <!-- KHỐI 3: SUPERSET & CSDL -->
    <div class="col" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="card" style="border-left: 4px solid #f59e0b;">
        <div class="card-header">
          <span style="font-size: 18px;">📊</span>
          <div class="card-title" style="color: #fbbf24;">Apache Superset API</div>
        </div>
        <div class="card-desc">Cổng REST API của Apache Superset quản lý việc xác thực JWT, tạo Chart Slice, cập nhật Dashboard Layout và cấp Guest Token.</div>
        <div class="card-tag" style="background: rgba(245, 158, 11, 0.15); color: #fde68a;">Superset Engine</div>
      </div>

      <div class="card" style="border-left: 4px solid #10b981;">
        <div class="card-header">
          <span style="font-size: 18px;">🗄️</span>
          <div class="card-title" style="color: #34d399;">Analytics Data Mart</div>
        </div>
        <div class="card-desc">Schema <code>analytics</code> gồm 6 bảng kết quả AI và 4 view nghiệp vụ; kết nối trực tiếp qua role bảo mật chỉ đọc <code>superset_ro</code>.</div>
        <div class="card-tag" style="background: rgba(16, 185, 129, 0.15); color: #6ee7b7;">PostgreSQL 16</div>
      </div>
    </div>
  </div>

  <div class="footer-legend">
    <div class="legend-item">
      <div class="legend-dot" style="background: #38bdf8;"></div>
      <span><strong>Tác nhân:</strong> Nhận lệnh tự nhiên và gọi MCP Tool chuẩn xác</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #a855f7;"></div>
      <span><strong>Authoring API:</strong> Tự động cấu hình biểu đồ không tạo trùng ID</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #f59e0b;"></div>
      <span><strong>Xác thực an toàn:</strong> Thao tác thay đổi bắt buộc xác nhận `confirm=true`</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #10b981;"></div>
      <span><strong>Chống tràn tải:</strong> Timeout 5 giây và transaction chỉ đọc</span>
    </div>
  </div>
</div>
</body>
</html>
"""

# 3. DIAGRAM: REPRODUCIBLE EVALUATION BENCHMARK (Mục 5)
HTML_EVALUATION = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
  .header h1 {{ color: #10b981; }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }}
  .metric-card {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    position: relative;
  }}
  .metric-val {{
    font-size: 32px;
    font-weight: 800;
    margin: 8px 0;
    letter-spacing: -0.5px;
  }}
  .metric-label {{
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
  }}
  .metric-sub {{
    font-size: 11.5px;
    color: #94a3b8;
    margin-top: 4px;
  }}

  .backtest-box {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px 24px;
  }}
  .backtest-title {{
    font-size: 15px;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .compare-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }}
  .compare-table th {{
    text-align: left;
    padding: 8px 12px;
    background: #1e293b;
    color: #94a3b8;
    border-bottom: 1px solid #334155;
    font-weight: 600;
  }}
  .compare-table td {{
    padding: 10px 12px;
    border-bottom: 1px solid #1e293b;
    color: #e2e8f0;
  }}
  .badge-win {{
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 11px;
  }}
  .badge-lose {{
    background: rgba(244, 63, 94, 0.2);
    color: #fb7185;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 11px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><span>📈</span> BẢNG ĐÁNH GIÁ THỰC NGHIỆM ĐỊNH LƯỢNG MÔ HÌNH AI & BACKTEST (MỤC 5)</h1>
    <p>Kết quả tái lập thực tế từ lệnh `python manage.py evaluate_ai_quality`: Minh bạch chỉ số và đối chứng Baseline</p>
  </div>

  <div class="metrics-grid">
    <div class="metric-card" style="border-top: 4px solid #38bdf8;">
      <div class="metric-label">Phân Khúc Hồ Sơ B2B</div>
      <div class="metric-val" style="color: #38bdf8;">7 / 7 (100%)</div>
      <div class="metric-sub">6 Gemini (85.7%) + 1 Rules Fallback (14.3%)<br/>1 hồ sơ không consent bị chặn an toàn</div>
    </div>

    <div class="metric-card" style="border-top: 4px solid #10b981;">
      <div class="metric-label">Phân Tích Cảm Xúc Tiếng Việt</div>
      <div class="metric-val" style="color: #34d399;">20 / 20 (100%)</div>
      <div class="metric-sub">Accuracy: 1.0 · Macro-F1: 1.0<br/>Đã xử lý cấu trúc phủ định tu từ</div>
    </div>

    <div class="metric-card" style="border-top: 4px solid #a855f7;">
      <div class="metric-label">Nhận Diện Nhóm Giải Pháp</div>
      <div class="metric-val" style="color: #c084fc;">8 / 8 (100%)</div>
      <div class="metric-sub">Nhận diện đúng nhu cầu CRM, Kho, POS, Hạ tầng chuyển đổi số</div>
    </div>

    <div class="metric-card" style="border-top: 4px solid #f59e0b;">
      <div class="metric-label">Dự Báo Doanh Thu (MAE)</div>
      <div class="metric-val" style="color: #fbbf24;">3,50 Triệu VNĐ</div>
      <div class="metric-sub">Lựa chọn thận trọng: <strong>Naive Baseline</strong><br/>Tốt hơn mô hình hồi quy tuyến tính cũ (4,43M)</div>
    </div>
  </div>

  <div class="backtest-box">
    <div class="backtest-title">
      <span>🔍</span> ĐỐI CHỨNG DỰ BÁO DOANH THU ROLLING-ORIGIN BACKTEST (4 THÁNG KIỂM ĐỊNH DEMO)
    </div>
    <table class="compare-table">
      <thead>
        <tr>
          <th>Mô hình / Phương pháp</th>
          <th>Cơ chế hoạt động</th>
          <th>Sai số tuyệt đối (MAE)</th>
          <th>So với Baseline</th>
          <th>Quyết định áp dụng</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Naive Baseline (Tháng cuối)</strong></td>
          <td>Lấy giá trị thực tế của tháng gần nhất làm dự báo</td>
          <td style="color: #34d399; font-weight: 700;">3.500.000 VNĐ</td>
          <td>Mốc chuẩn (0%)</td>
          <td><span class="badge-win">CHỌN SỬ DỤNG</span> (Tránh rủi ro tài chính)</td>
        </tr>
        <tr>
          <td><strong>Hồi quy Tuyến tính (Linear)</strong></td>
          <td>Hồi quy xu hướng trên chuỗi lịch sử quá ngắn</td>
          <td style="color: #fb7185; font-weight: 700;">4.431.953 VNĐ</td>
          <td>Tệ hơn 26.6%</td>
          <td><span class="badge-lose">TỪ CHỐI</span> (Chưa đủ 18 tháng dữ liệu)</td>
        </tr>
        <tr>
          <td><strong>Trung bình trượt 3 tháng (Mean 3)</strong></td>
          <td>San phẳng biến động ngắn hạn</td>
          <td style="color: #94a3b8;">Chưa kích hoạt</td>
          <td>Chưa đủ điều kiện</td>
          <td>Chỉ kích hoạt khi lịch sử &ge; 18 tháng</td>
        </tr>
      </tbody>
    </table>
    <div style="font-size: 11.5px; color: #94a3b8; margin-top: 12px; line-height: 1.45;">
      * <em>Nguyên tắc học thuật minh bạch:</em> Kết quả đo lường trên bộ kịch bản B2B phát triển. Hệ thống lựa chọn mô hình đơn giản nhưng kiểm chứng được, không vội vàng áp dụng mô hình phức tạp khi chưa có bằng chứng vượt Baseline.
    </div>
  </div>

  <div class="footer-legend">
    <div class="legend-item">
      <div class="legend-dot" style="background: #38bdf8;"></div>
      <span><strong>Phân loại hồ sơ:</strong> Ghi nhận tỷ lệ fallback độc lập, không gộp vào Gemini</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #10b981;"></div>
      <span><strong>Cảm xúc:</strong> Xử lý câu mỉa mai và phủ định tu từ theo mẫu ngữ pháp</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #f59e0b;"></div>
      <span><strong>Dự báo:</strong> Tiêu chuẩn khắt khe: chỉ thay thế Baseline nếu tốt hơn &ge; 10%</span>
    </div>
  </div>
</div>
</body>
</html>
"""

# 4. DIAGRAM: AI ROADMAP & DECISION GATES (Mục 7.3 - Checklist 6)
HTML_ROADMAP = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
  .header h1 {{ color: #fbbf24; }}
  .road-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
  }}
  .step-card {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    position: relative;
  }}
  .step-head {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 8px;
  }}
  .step-badge-letter {{
    width: 26px;
    height: 26px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .step-name {{
    font-size: 14px;
    font-weight: 700;
  }}
  .gate-box {{
    margin-top: 12px;
    background: #1e293b;
    border-left: 3px solid #fbbf24;
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 11px;
    color: #e2e8f0;
  }}
  .gate-title {{
    font-size: 10px;
    font-weight: 700;
    color: #fbbf24;
    text-transform: uppercase;
    margin-bottom: 3px;
  }}
  
  /* Steps color */
  .st-a {{ border-top: 4px solid #38bdf8; }}
  .st-a .step-badge-letter {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; }}
  .st-a .step-name {{ color: #38bdf8; }}

  .st-b {{ border-top: 4px solid #10b981; }}
  .st-b .step-badge-letter {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
  .st-b .step-name {{ color: #34d399; }}

  .st-c {{ border-top: 4px solid #a855f7; }}
  .st-c .step-badge-letter {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; }}
  .st-c .step-name {{ color: #c084fc; }}

  .st-d {{ border-top: 4px solid #06b6d4; }}
  .st-d .step-badge-letter {{ background: rgba(6, 182, 212, 0.2); color: #22d3ee; }}
  .st-d .step-name {{ color: #22d3ee; }}

  .st-e {{ border-top: 4px solid #f43f5e; }}
  .st-e .step-badge-letter {{ background: rgba(244, 63, 94, 0.2); color: #fb7185; }}
  .st-e .step-name {{ color: #fb7185; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><span>🗺️</span> LỘ TRÌNH 5 BƯỚC TRIỂN KHAI AI & CỔNG KIỂM SOÁT QUYẾT ĐỊNH (MỤC 7.3)</h1>
    <p>Quy trình kiểm định và chuyển giao khoa học: Đảm bảo mô hình AI mới luôn vượt trội trước khi đưa vào vận hành</p>
  </div>

  <div class="road-grid">
    <!-- BƯỚC A -->
    <div class="step-card st-a">
      <div class="step-head">
        <div class="step-badge-letter">A</div>
        <div class="step-name">Chuẩn Hóa Dữ Liệu</div>
      </div>
      <div class="card-desc" style="font-size: 11.5px;">
        • Danh mục nguồn & Consent.<br/>
        • Từ điển nhãn WON/LOST.<br/>
        • Phân tách Train / Val / Test theo thời gian và doanh nghiệp để tránh rò rỉ dữ liệu.
      </div>
      <div class="gate-box">
        <div class="gate-title">CỔNG QUYẾT ĐỊNH A &rarr; B</div>
        Nguồn hợp lệ, không rò rỉ nhãn tương lai, đủ số mẫu từng lớp.
      </div>
    </div>

    <!-- BƯỚC B -->
    <div class="step-card st-b">
      <div class="step-head">
        <div class="step-badge-letter">B</div>
        <div class="step-name">Chạy Đối Chứng</div>
      </div>
      <div class="card-desc" style="font-size: 11.5px;">
        • Đo lường cùng tập dữ liệu cho Rules, mô hình đơn giản và ứng viên (PhoBERT, K-Means).<br/>
        • Ghi log Model Version, latency, chi phí token.
      </div>
      <div class="gate-box">
        <div class="gate-title">CỔNG QUYẾT ĐỊNH B &rarr; C</div>
        Metric tính từ dự đoán thật; công bố mọi fold, fallback & ca sai.
      </div>
    </div>

    <!-- BƯỚC C -->
    <div class="step-card st-c">
      <div class="step-head">
        <div class="step-badge-letter">C</div>
        <div class="step-name">So Sánh & Lựa Chọn</div>
      </div>
      <div class="card-desc" style="font-size: 11.5px;">
        • Bảng đánh giá đa tiêu chí (Chất lượng / Tốc độ / Chi phí).<br/>
        • Phân tích tác động lên nhóm khách hàng bị suy giảm độ chính xác.
      </div>
      <div class="gate-box">
        <div class="gate-title">CỔNG QUYẾT ĐỊNH C &rarr; D</div>
        Chỉ thay thế cách cũ nếu vượt trội tiêu chí; dự báo phải hơn Baseline &ge;10%.
      </div>
    </div>

    <!-- BƯỚC D -->
    <div class="step-card st-d">
      <div class="step-head">
        <div class="step-badge-letter">D</div>
        <div class="step-name">Đưa Lên BI Superset</div>
      </div>
      <div class="card-desc" style="font-size: 11.5px;">
        • Bổ sung trường Model Version, Batch ID, Sample Size.<br/>
        • Xây dựng biểu đồ so sánh song song giữa Baseline và mô hình ứng viên.
      </div>
      <div class="gate-box">
        <div class="gate-title">CỔNG QUYẾT ĐỊNH D &rarr; E</div>
        Rà soát schema & migration riêng; kiểm tra quyền đọc qua superset_ro.
      </div>
    </div>

    <!-- BƯỚC E -->
    <div class="step-card st-e">
      <div class="step-head">
        <div class="step-badge-letter">E</div>
        <div class="step-name">Thí Điểm Có Người Duyệt</div>
      </div>
      <div class="card-desc" style="font-size: 11.5px;">
        • Thử nghiệm giao diện với nhân viên sales thực tế.<br/>
        • Đo lường tỷ lệ hoàn tất việc chăm sóc và tỷ lệ chuyển đổi ROI thực tế.
      </div>
      <div class="gate-box">
        <div class="gate-title">CỔNG NGHIỆM THU CUỐI</div>
        Luôn có kế hoạch Rollback an toàn; AI không tự gửi liên hệ ra ngoài.
      </div>
    </div>
  </div>

  <div class="footer-legend">
    <div class="legend-item">
      <div class="legend-dot" style="background: #38bdf8;"></div>
      <span><strong>Kiểm định nghiêm ngặt:</strong> Khóa tập Test độc lập, chống Overfitting</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #a855f7;"></div>
      <span><strong>Chiến lược chọn mô hình:</strong> Tên thuật toán phức tạp không thay thế được thực nghiệm</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot" style="background: #f43f5e;"></div>
      <span><strong>Human-in-the-loop:</strong> Nhân viên luôn là người ra quyết định cuối cùng</span>
    </div>
  </div>
</div>
</body>
</html>
"""

DIAGRAMS = [
    ("so-do-bao-mat-consent-phan-quyen.png", HTML_SECURITY, 1500, 800),
    ("kien-truc-superset-mcp-agent.png", HTML_MCP, 1500, 880),
    ("bieu-do-danh-gia-ai-thuc-nghiem.png", HTML_EVALUATION, 1500, 800),
    ("lo-trinh-5-buoc-ai-decision-gates.png", HTML_ROADMAP, 1500, 800),
]

def main():
    out_dir = Path("docs/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Bat dau tao 4 so do truc quan cho bao cao ky thuat...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for filename, html_content, width, height in DIAGRAMS:
            out_file = out_dir / filename
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=2
            )
            page.set_content(html_content)
            page.wait_for_timeout(400)
            container = page.locator(".container")
            container.screenshot(path=str(out_file))
            page.close()
            print(f"✅ Da tao {filename} ({out_file.stat().st_size} bytes)")
        browser.close()
    print("Hoan tat tao toan bo so do!")

if __name__ == "__main__":
    main()
