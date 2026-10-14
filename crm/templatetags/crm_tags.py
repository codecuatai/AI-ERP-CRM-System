from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="format_currency")
def format_currency(value):
    """Format numeric values as Vietnamese currency with dot thousand separator.
    e.g. 18500000 -> 18.500.000 đ
    """
    if value is None or value == "":
        return "0 đ"
    try:
        num = int(float(value))
        formatted = f"{num:,}".replace(",", ".")
        return f"{formatted} đ"
    except (ValueError, TypeError):
        return f"{value} đ"


@register.filter(name="segment_badge")
def segment_badge(segment):
    """Render a semantic styled badge for customer AI segment."""
    if not segment or segment == "Chưa phân loại":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">'
            'Chưa phân loại</span>'
        )
    elif segment == "VIP":
        return mark_safe(
            '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 shadow-sm">'
            '<svg class="w-3 h-3 text-purple-600" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>'
            'VIP</span>'
        )
    elif segment == "Tiềm năng":
        return mark_safe(
            '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">'
            '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>'
            'Tiềm năng</span>'
        )
    elif segment == "Nguy cơ rời bỏ":
        return mark_safe(
            '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 shadow-sm">'
            '<span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>'
            'Nguy cơ rời bỏ</span>'
        )
    elif segment == "Ngủ đông":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">'
            'Ngủ đông</span>'
        )
    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{segment}</span>'
    )


@register.filter(name="priority_reason_badge")
def priority_reason_badge(reason):
    """Render semantic badge for priority customer reason."""
    reason_str = str(reason).strip()
    reason_lower = reason_str.lower()
    
    if "quá hạn" in reason_lower:
        return mark_safe(
            f'<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">'
            f'<svg class="w-3 h-3 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
            f'{reason_str}</span>'
        )
    elif "vip" in reason_lower:
        return mark_safe(
            f'<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">'
            f'<svg class="w-3 h-3 text-purple-500" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>'
            f'{reason_str}</span>'
        )
    elif "nguy cơ" in reason_lower or "rời bỏ" in reason_lower:
        return mark_safe(
            f'<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200">'
            f'{reason_str}</span>'
        )
    elif "điểm" in reason_lower:
        return mark_safe(
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">'
            f'{reason_str}</span>'
        )
    else:
        return mark_safe(
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200">'
            f'{reason_str}</span>'
        )


@register.filter(name="task_status_badge")
def task_status_badge(status_label):
    """Render semantic badge for care task status."""
    label = str(status_label).strip()
    if label == "Cần làm":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">Cần làm</span>'
        )
    elif label == "Đang làm":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">Đang làm</span>'
        )
    elif label == "Hoàn tất":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Hoàn tất</span>'
        )
    return mark_safe(f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{label}</span>')


@register.filter(name="task_priority_badge")
def task_priority_badge(priority_label):
    """Render semantic badge for care task priority."""
    label = str(priority_label).strip()
    if label == "Cao":
        return mark_safe(
            '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">Ưu tiên cao</span>'
        )
    elif label == "Vừa":
        return mark_safe(
            '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">Vừa</span>'
        )
    elif label == "Thấp":
        return mark_safe(
            '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-50 text-slate-500 border border-slate-200">Thấp</span>'
        )
    return mark_safe(f'<span class="text-xs text-slate-600">{label}</span>')


@register.filter(name="lead_status_badge")
def lead_status_badge(status_label):
    """Render semantic badge for lead request status."""
    label = str(status_label).strip()
    if label == "Mới gửi":
        return mark_safe(
            '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 shadow-sm">'
            '<span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>Mới gửi</span>'
        )
    elif label == "Đã liên hệ":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 shadow-sm">Đã liên hệ</span>'
        )
    elif label == "Đã xử lý":
        return mark_safe(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">Đã xử lý</span>'
        )
    return mark_safe(f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{label}</span>')


@register.filter(name="is_ai_chat")
def is_ai_chat(subject):
    """Check if the interaction subject represents an AI chatbot session."""
    return bool(subject and "Trợ lý AI" in str(subject))


@register.filter(name="interaction_marker")
def interaction_marker(item):
    """Render semantic styled icon marker for timeline item."""
    subject = str(getattr(item, "subject", ""))
    kind = str(getattr(item, "kind", ""))

    if "Trợ lý AI" in subject:
        return mark_safe(
            '<span class="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-tr from-indigo-600 to-blue-600 text-white text-xs shadow-xs" title="Hội thoại cùng Trợ lý AI">🤖</span>'
        )
    elif kind == "EMAIL":
        return mark_safe(
            '<span class="grid h-8 w-8 place-items-center rounded-full bg-blue-100 text-blue-700 text-xs font-bold" title="Email">✉</span>'
        )
    elif kind == "PHONE":
        return mark_safe(
            '<span class="grid h-8 w-8 place-items-center rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold" title="Cuộc gọi">📞</span>'
        )
    elif kind == "MEETING":
        return mark_safe(
            '<span class="grid h-8 w-8 place-items-center rounded-full bg-purple-100 text-purple-700 text-xs font-bold" title="Cuộc họp">🤝</span>'
        )
    return mark_safe(
        '<span class="grid h-8 w-8 place-items-center rounded-full bg-slate-100 text-slate-600 text-xs font-bold" title="Ghi chú">📝</span>'
    )


@register.filter(name="render_chat_transcript")
def render_chat_transcript(content):
    """Format AI chat transcript into modern interactive chat bubbles."""
    import html
    if not content:
        return ""

    lines = str(content).strip().splitlines()
    bubbles = []
    current_role = None
    current_text = []

    def flush_bubble():
        if not current_role or not current_text:
            return
        text = html.escape("\n".join(current_text))
        text_formatted = text.replace("\n", "<br>")
        if current_role == "user":
            bubbles.append(
                f'<div class="flex items-start gap-2.5 my-2.5 max-w-[90%]">'
                f'  <span class="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-slate-200 text-slate-700 text-xs font-bold shadow-2xs" title="Khách hàng">👤</span>'
                f'  <div class="flex-1 rounded-2xl rounded-tl-xs bg-slate-100/90 border border-slate-200/80 px-3.5 py-2.5 text-xs text-slate-800 leading-relaxed shadow-2xs">'
                f'    <div class="flex items-center justify-between mb-1">'
                f'      <strong class="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Khách hàng</strong>'
                f'    </div>'
                f'    <div>{text_formatted}</div>'
                f'  </div>'
                f'</div>'
            )
        else:
            bubbles.append(
                f'<div class="flex items-start gap-2.5 my-2.5 max-w-[95%]">'
                f'  <span class="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white text-xs font-bold shadow-xs" title="Trợ lý AI DigiFlow">🤖</span>'
                f'  <div class="flex-1 rounded-2xl rounded-tl-xs bg-gradient-to-br from-blue-50/90 to-indigo-50/50 border border-blue-100 px-3.5 py-2.5 text-xs text-slate-900 leading-relaxed shadow-2xs">'
                f'    <div class="flex items-center justify-between mb-1">'
                f'      <strong class="text-[10px] uppercase font-bold text-blue-700 tracking-wider flex items-center gap-1"><span>DigiFlow AI</span><span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500"></span></strong>'
                f'    </div>'
                f'    <div class="text-slate-800">{text_formatted}</div>'
                f'  </div>'
                f'</div>'
            )

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("Khách hàng:") or line_stripped.startswith("Khách:"):
            flush_bubble()
            current_role = "user"
            prefix = "Khách hàng:" if line_stripped.startswith("Khách hàng:") else "Khách:"
            current_text = [line_stripped[len(prefix):].strip()]
        elif line_stripped.startswith("DigiFlow AI:") or line_stripped.startswith("AI:"):
            flush_bubble()
            current_role = "bot"
            prefix = "DigiFlow AI:" if line_stripped.startswith("DigiFlow AI:") else "AI:"
            current_text = [line_stripped[len(prefix):].strip()]
        else:
            if current_role:
                current_text.append(line_stripped)
            else:
                current_role = "user"
                current_text = [line_stripped]

    flush_bubble()

    if not bubbles:
        return mark_safe(f'<p class="text-xs text-slate-700 leading-relaxed">{html.escape(content)}</p>')

    count = len(bubbles)
    rendered = "".join(bubbles)
    return mark_safe(
        f'<div class="rounded-xl border border-indigo-100 bg-white p-3.5 shadow-2xs my-1">'
        f'  <div class="flex items-center justify-between border-b border-indigo-50 pb-2 mb-2 text-xs">'
        f'    <span class="inline-flex items-center gap-1.5 font-bold text-indigo-900">'
        f'      <span class="relative flex h-2 w-2">'
        f'        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>'
        f'        <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-600"></span>'
        f'      </span>'
        f'      Trích xuất phiên tư vấn tự động ({count} tin nhắn)'
        f'    </span>'
        f'    <span class="text-[11px] text-slate-400 font-medium">Website Assistant 24/7</span>'
        f'  </div>'
        f'  <div class="space-y-1 max-h-[450px] overflow-y-auto pr-1">'
        f'    {rendered}'
        f'  </div>'
        f'</div>'
    )


@register.filter(name="render_ai_checklist")
def render_ai_checklist(recommendation, customer_pk=None):
    """Format AI recommendations into structured, actionable checklist cards with direct task creation."""
    import html
    import re
    from django.urls import reverse
    from django.utils.http import urlencode

    if not recommendation:
        return ""

    text = str(recommendation).strip()

    # Split recommendation text into individual checklist blocks
    pattern = re.compile(r'(?:^|\n\n+)(?=Checklist\s*\d+|Mục\s*\d+|Bước\s*\d+|\d+\.\s+)', re.IGNORECASE)
    parts = [p.strip() for p in pattern.split(text) if p.strip()]

    if not parts or (len(parts) == 1 and not re.match(r'^(?:Checklist|Mục|Bước|\d+\.)', parts[0], re.IGNORECASE)):
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(parts) <= 1:
            parts = [p.strip() for p in text.split("\n") if p.strip()]

    cards = []
    for idx, part in enumerate(parts, 1):
        lines = [line.strip() for line in part.splitlines() if line.strip()]
        if not lines:
            continue

        first_line = lines[0]
        # Clean title prefix
        clean_title = re.sub(
            r'^(?:Checklist\s*\d+[:.]?|Mục\s*\d+[:.]?|Bước\s*\d+[:.]?|\d+\.[:.]?)\s*',
            '',
            first_line,
            flags=re.IGNORECASE,
        ).strip()
        if not clean_title:
            clean_title = first_line

        # Format details
        body_lines = lines[1:] if len(lines) > 1 else []
        body_html_parts = []
        for bl in body_lines:
            bl_clean = re.sub(r'^[-•*☑\[\]\s]+', '', bl).strip()
            if bl_clean:
                bl_formatted = html.escape(bl_clean)
                for label in (
                    "Hành động cụ thể:",
                    "Hành động:",
                    "Mục tiêu:",
                    "Thời hạn khuyến nghị:",
                    "Thời hạn:",
                ):
                    if bl_formatted.startswith(label):
                        bl_formatted = f'<strong class="text-slate-900 font-semibold">{label}</strong> ' + bl_formatted[len(label):].strip()
                        break
                body_html_parts.append(
                    f'<li class="flex items-start gap-2 py-0.5">'
                    f'  <span class="text-blue-500 font-bold shrink-0 mt-0.5">›</span>'
                    f'  <span class="text-slate-700">{bl_formatted}</span>'
                    f'</li>'
                )

        create_task_url = ""
        if customer_pk:
            params = urlencode({"title": clean_title[:180], "desc": "\n".join(body_lines)})
            create_task_url = f"{reverse('crm:customer_care_task_create', args=[customer_pk])}?{params}"

        action_btn_html = ""
        if create_task_url:
            action_btn_html = (
                f'<a href="{create_task_url}" class="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 hover:text-blue-800 border border-blue-200/90 px-3 py-1 rounded-lg transition-all shadow-2xs">'
                f'  <span>＋ Tạo việc chăm sóc từ mục này</span>'
                f'</a>'
            )

        body_html = ""
        if body_html_parts:
            body_html = f'<ul class="mt-2.5 space-y-1 text-xs leading-relaxed pl-0 list-none border-t border-slate-100 pt-2">' + "".join(body_html_parts) + '</ul>'

        cards.append(
            f'<div class="rounded-xl border border-blue-100/90 bg-white p-4 shadow-2xs hover:border-blue-300 hover:shadow-xs transition-all my-3">'
            f'  <div class="flex items-start justify-between gap-3 flex-wrap">'
            f'    <div class="flex items-start gap-3 min-w-0 flex-1">'
            f'      <div class="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-blue-600 text-white font-bold text-xs shadow-2xs" title="Mục việc trong Checklist">'
            f'        ✓'
            f'      </div>'
            f'      <div class="min-w-0 flex-1">'
            f'        <div class="flex items-center gap-2 flex-wrap mb-1">'
            f'          <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">Checklist #{idx}</span>'
            f'          <strong class="text-sm font-bold text-slate-900 leading-snug">{html.escape(clean_title)}</strong>'
            f'        </div>'
            f'        {body_html}'
            f'      </div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-end">'
            f'    {action_btn_html}'
            f'  </div>'
            f'</div>'
        )

    return mark_safe("".join(cards))


