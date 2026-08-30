import streamlit as st
import streamlit.components.v1 as components
import requests
import uuid
import re
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

BACKEND_URL = "http://localhost:8000"


def generate_gap_analysis_pdf(doc_a: str, doc_b: str, analysis_text: str) -> bytes:
    """
    Generates a formatted PDF report for the ITU AI Readiness Gap Analysis.
    Returns the PDF as bytes ready for download.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # === Register a Unicode-capable font that supports Arabic + Latin ===
    font_name = "Helvetica"
    font_name_bold = "Helvetica-Bold"
    for candidate in [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]:
        if os.path.exists(candidate):
            try:
                pdfmetrics.registerFont(TTFont("UniFont", candidate))
                font_name = "UniFont"
                break
            except Exception:
                continue
    for bold_candidate in [
        r"C:\Windows\Fonts\tahomabd.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
    ]:
        if os.path.exists(bold_candidate):
            try:
                pdfmetrics.registerFont(TTFont("UniFontBold", bold_candidate))
                font_name_bold = "UniFontBold"
                break
            except Exception:
                continue

    styles = getSampleStyleSheet()

    # === Arabic text reshaping support ===
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        _has_arabic_support = True
    except ImportError:
        _has_arabic_support = False

    def reshape_arabic(text: str) -> str:
        """Reshape Arabic text for correct PDF rendering (RTL + glyph joining)."""
        if not _has_arabic_support:
            return text
        # Only reshape segments that contain Arabic characters
        if not re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            return text
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text

    # === Normalize problematic Unicode characters ===
    def normalize_text(text: str) -> str:
        replacements = {
            '\u2011': '-', '\u2010': '-', '\u2012': '-', '\u2013': '-',
            '\u2014': '-', '\u2015': '-', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2026': '...',
            '\u00a0': ' ', '\u200b': '', '\u200c': '', '\u200d': '', '\ufeff': '',
            '\u2022': '-',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def prepare_text_for_pdf(text: str) -> str:
        """Normalize Unicode AND reshape Arabic for PDF rendering."""
        text = normalize_text(text)
        # Reshape Arabic segments within the text
        def reshape_match(m):
            return reshape_arabic(m.group(0))
        # Find Arabic runs (including surrounding punctuation/spaces)
        text = re.sub(
            r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
            r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\.,;:\-\(\)\"\']*',
            reshape_match,
            text
        )
        return text

    analysis_text = prepare_text_for_pdf(analysis_text)
    doc_a = normalize_text(doc_a)
    doc_b = normalize_text(doc_b)

    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"],
        fontName=font_name_bold, fontSize=18, textColor=colors.HexColor("#1a237e"),
        spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("SubTitle", parent=styles["Normal"],
        fontName=font_name, fontSize=11, textColor=colors.HexColor("#5c6bc0"),
        spaceAfter=4, alignment=TA_CENTER)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#455a64"),
        spaceAfter=3, leftIndent=10)
    heading_style = ParagraphStyle("SectionHeading", parent=styles["Heading2"],
        fontName=font_name_bold, fontSize=13, textColor=colors.HexColor("#283593"),
        spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#212121"),
        spaceAfter=5, leading=15)
    bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#212121"),
        spaceAfter=3, leftIndent=18, bulletIndent=6, leading=14)

    def safe_paragraph(text: str, style) -> Paragraph:
        try:
            return Paragraph(text, style)
        except Exception:
            plain = re.sub(r'<[^>]+>', '', text)
            try:
                return Paragraph(plain, style)
            except Exception:
                return Paragraph("(rendering error)", style)

    story = []

    # === Header ===
    story.append(safe_paragraph("ITU AI Readiness 2.0", title_style))
    story.append(safe_paragraph("Policy Gap Analysis Report", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3949ab")))
    story.append(Spacer(1, 0.4 * cm))

    # === Metadata table ===
    meta_data = [
        [safe_paragraph("<b>Document A:</b>", meta_style), safe_paragraph(doc_a.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"), meta_style)],
        [safe_paragraph("<b>Document B:</b>", meta_style), safe_paragraph(doc_b.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"), meta_style)],
        [safe_paragraph("<b>Framework:</b>", meta_style), safe_paragraph("ITU AI Readiness 2.0 - 13 Dimensions &amp; ITU-T Y.3172 Pipeline", meta_style)],
        [safe_paragraph("<b>Generated:</b>", meta_style), safe_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), meta_style)],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 13 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#eeeeee"), colors.HexColor("#fafafa")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5cae9")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c5cae9")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9fa8da")))

    # === Analysis body ===
    in_table = False
    table_data = []
    in_mermaid = False

    def flush_table():
        if not table_data:
            return
        max_cols = max(len(row) for row in table_data)
        for row in table_data:
            while len(row) < max_cols:
                row.append(safe_paragraph("", body_style))
        col_widths = [(17.0 / max_cols) * cm for _ in range(max_cols)]
        tbl = Table(table_data, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaf6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8f9ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5cae9")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.4 * cm))
        table_data.clear()

    for line in analysis_text.splitlines():
        stripped = line.strip()

        # Skip mermaid code blocks
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid:
            if stripped.startswith("```"):
                in_mermaid = False
            continue
        if stripped.startswith("```"):
            continue

        # Markdown table line?
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            # Skip separator lines (|---|---|)
            if re.match(r"^\|[\s\-:]+\|", stripped) and not re.search(r'[a-zA-Z\u0600-\u06FF]', stripped):
                continue
            clean_line = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            clean_line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", clean_line)
            clean_line = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean_line)
            cells = clean_line.split("|")[1:-1]
            row = [safe_paragraph(cell.strip(), body_style) for cell in cells]
            table_data.append(row)
            continue

        if in_table:
            flush_table()
            in_table = False

        if not stripped:
            story.append(Spacer(1, 0.2 * cm))
            continue

        clean = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", clean)
        clean = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean)

        if stripped.startswith("# "):
            story.append(safe_paragraph(clean[2:], heading_style))
        elif stripped.startswith("## "):
            story.append(safe_paragraph(clean[3:], heading_style))
        elif stripped.startswith("### "):
            story.append(safe_paragraph(clean[4:], heading_style))
        elif stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c5cae9")))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            story.append(safe_paragraph("- " + clean[2:], bullet_style))
        elif re.match(r"^\d+\.", stripped):
            story.append(safe_paragraph(clean, bullet_style))
        else:
            story.append(safe_paragraph(clean, body_style))

    if in_table:
        flush_table()

    # === Footer ===
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3949ab")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(safe_paragraph(
        "Generated by NTU CET RAG Policy Analysis System - Powered by ITU AI Readiness 2.0 Framework",
        ParagraphStyle("Footer", parent=styles["Normal"], fontName=font_name, fontSize=8,
                       textColor=colors.HexColor("#9e9e9e"), alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()


st.set_page_config(
    page_title="Chat with your Documents",
    page_icon="📄",
    layout="wide",
)


def is_arabic(text: str) -> bool:
    """Checks whether the text contains Arabic characters."""
    return bool(re.search(r'[\u0600-\u06FF]', str(text or '')))


# Inject global Arabic typography and RTL stylesheet
st.markdown("""
<style>
/* Arabic RTL Typography and Layout */
.arabic-rtl {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif !important;
    line-height: 1.8 !important;
}
.arabic-rtl ol, .arabic-rtl ul {
    padding-right: 1.5rem !important;
    padding-left: 0 !important;
}
.arabic-quote {
    border-right: 4px solid #7c3aed !important;
    border-left: none !important;
    padding-right: 10px !important;
    padding-left: 0 !important;
    text-align: right !important;
    direction: rtl !important;
    font-style: italic;
    color: #888;
    font-size: 0.9em;
    margin-bottom: 8px;
}
.english-quote {
    border-left: 4px solid #7c3aed !important;
    border-right: none !important;
    padding-left: 10px !important;
    padding-right: 0 !important;
    text-align: left !important;
    direction: ltr !important;
    font-style: italic;
    color: #888;
    font-size: 0.9em;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


def sanitize_mermaid_code(code: str) -> str:
    """
    Sanitizes LLM-generated Mermaid code to prevent parse errors.
    Strips HTML tags, fixes unquoted node labels, and cleans up common issues.
    """
    # Remove any HTML tags that the LLM may have injected (e.g., <div>, </div>, <br>)
    code = re.sub(r'</?[a-zA-Z][^>]*>', '', code)
    # Remove zero-width and non-breaking spaces
    code = code.replace('\u200b', '').replace('\u00a0', ' ')
    # Fix node labels: ensure text inside brackets [] is quoted if it contains spaces or special chars
    # Pattern: A[unquoted text with spaces] -> A["unquoted text with spaces"]
    def quote_node_label(m):
        prefix = m.group(1)  # e.g., A
        bracket_open = m.group(2)  # [ or (
        label = m.group(3)  # the text inside
        bracket_close = m.group(4)  # ] or )
        # Already quoted
        if label.startswith('"') and label.endswith('"'):
            return f'{prefix}{bracket_open}{label}{bracket_close}'
        # Needs quoting if it has spaces, parens, Arabic, or special chars
        if re.search(r'[\s\(\)\u0600-\u06FF&<>]', label):
            escaped = label.replace('"', "'")
            return f'{prefix}{bracket_open}"{escaped}"{bracket_close}'
        return m.group(0)

    code = re.sub(
        r'([A-Za-z0-9_]+)\s*(\[)\s*([^\]]+?)\s*(\])',
        quote_node_label,
        code
    )
    code = re.sub(
        r'([A-Za-z0-9_]+)\s*(\()\s*([^\)]+?)\s*(\))',
        quote_node_label,
        code
    )
    # Remove completely empty lines that could confuse the parser
    lines = [l for l in code.splitlines() if l.strip()]
    return '\n'.join(lines)


def render_content_with_mermaid(content: str, key_prefix: str = "msg"):
    """
    Renders message content with automatic Arabic RTL detection and Mermaid diagram support.
    """
    pattern = r"```mermaid\s*\n(.*?)\n```"
    parts = re.split(pattern, content, flags=re.DOTALL)

    if len(parts) == 1:
        if is_arabic(content):
            st.markdown(f'<div class="arabic-rtl">\n\n{content}\n\n</div>', unsafe_allow_html=True)
        else:
            st.markdown(content)
        return

    for i, part in enumerate(parts):
        if not part.strip():
            continue
        if i % 2 == 0:
            if is_arabic(part):
                st.markdown(f'<div class="arabic-rtl">\n\n{part}\n\n</div>', unsafe_allow_html=True)
            else:
                st.markdown(part)
        else:
            mermaid_code = sanitize_mermaid_code(part.strip())
            html_code = f"""
            <div id="mermaid-container-{key_prefix}-{i}" style="display:flex; justify-content:center; align-items:center; background:#0f172a; border:1px solid #334155; border-radius:8px; padding:16px; margin:10px 0; overflow-x:auto;">
                <pre class="mermaid" style="margin:0; background:transparent; font-family:sans-serif;">
{mermaid_code}
                </pre>
            </div>
            <div id="mermaid-error-{key_prefix}-{i}" style="display:none; background:#1e1b2e; border:1px solid #7c3aed; border-radius:8px; padding:16px; margin:10px 0; color:#c4b5fd; font-family:monospace; font-size:0.85rem;">
                <b>⚠️ Diagram could not be rendered.</b><br>
                <pre style="white-space:pre-wrap; margin-top:8px; color:#94a3b8;">{mermaid_code}</pre>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: false, theme: 'dark' }});
                try {{
                    await mermaid.run({{ querySelector: '#mermaid-container-{key_prefix}-{i} .mermaid' }});
                }} catch (e) {{
                    document.getElementById('mermaid-container-{key_prefix}-{i}').style.display = 'none';
                    document.getElementById('mermaid-error-{key_prefix}-{i}').style.display = 'block';
                }}
            </script>
            """
            components.html(html_code, height=350, scrolling=True)
            with st.expander("🔍 View Chart Code (Mermaid)", expanded=False):
                st.code(mermaid_code, language="mermaid")



# Initialize session state variables
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = f"sess_{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "reply_target" not in st.session_state:
    st.session_state.reply_target = None

if "pending_turn" not in st.session_state:
    st.session_state.pending_turn = None

is_busy = (st.session_state.pending_turn is not None)

st.title("📄 Chat with your Documents")
st.caption("Powered by RAG — Retrieval Augmented Generation")

with st.sidebar:
    # === Chat Sessions Manager ===
    st.header("💬 Chat Sessions")
    col_new, col_ref_s = st.columns([4, 1])
    with col_new:
        if st.button("➕ New Chat", type="primary", use_container_width=True, disabled=is_busy, help="Start a new conversation"):
            st.session_state.current_session_id = f"sess_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.session_state.reply_target = None
            st.session_state.pending_turn = None
            st.rerun()
    with col_ref_s:
        if st.button("🔄", key="ref_sessions_btn", disabled=is_busy, help="Refresh session list"):
            st.rerun()

    # List saved sessions
    try:
        sess_resp = requests.get(f"{BACKEND_URL}/sessions", timeout=3).json()
        saved_sessions = sess_resp.get("sessions", [])
        if saved_sessions:
            for s in saved_sessions[:8]:
                s_id = s["id"]
                s_title = s["title"]
                is_active = (s_id == st.session_state.current_session_id)
                display_title = (s_title[:20] + "...") if len(s_title) > 23 else s_title
                prefix = "▶ " if is_active else "💬 "

                col_s_btn, col_s_del = st.columns([5, 1])
                with col_s_btn:
                    if st.button(f"{prefix}{display_title}", key=f"sess_{s_id}", disabled=is_busy, help=f"{s_title} ({s['message_count']} msgs)"):
                        full_sess = requests.get(f"{BACKEND_URL}/sessions/{s_id}", timeout=3).json()
                        if "session" in full_sess and full_sess["session"]:
                            st.session_state.current_session_id = s_id
                            st.session_state.messages = full_sess["session"]["messages"]
                            st.session_state.reply_target = None
                            st.rerun()
                with col_s_del:
                    if st.button("🗑️", key=f"delsess_{s_id}", disabled=is_busy, help=f"Delete session '{s_title}'"):
                        requests.delete(f"{BACKEND_URL}/sessions/{s_id}", timeout=3)
                        if st.session_state.current_session_id == s_id:
                            st.session_state.current_session_id = f"sess_{uuid.uuid4().hex[:8]}"
                            st.session_state.messages = []
                            st.session_state.reply_target = None
                        st.rerun()
        else:
            st.caption("No saved chats yet")
    except Exception:
        st.caption("⚠️ Could not load sessions")

    st.divider()

    col_hdr, col_btn = st.columns([5, 1])
    with col_hdr:
        st.header("🧠 Select Model")
    with col_btn:
        if st.button("🔄", key="ref_models_btn", disabled=is_busy, help="Refresh available models from server"):
            try:
                st.session_state.available_models = requests.get(f"{BACKEND_URL}/models", timeout=10).json()
                st.rerun()
            except Exception:
                pass
    st.caption("Choose between a local model running on your machine or a cloud API with your own key")

    # Fetch available models from backend once and store in session state
    if "available_models" not in st.session_state:
        try:
            st.session_state.available_models = requests.get(f"{BACKEND_URL}/models", timeout=10).json()
        except Exception:
            st.session_state.available_models = {"local_models": [], "local_available": False, "cloud_providers": {}}

    models_info = st.session_state.available_models

    mode = st.radio(
        "Generation Mode",
        options=["Local Model (Free, No API Key)", "Cloud API (Requires Your API Key)"],
        index=0 if models_info["local_available"] else 1,
        disabled=is_busy,
    )

    if mode.startswith("Local Model"):
        provider = "ollama"
        api_key = None
        if models_info["local_models"]:
            model = st.selectbox("Detected Local Model", options=models_info["local_models"], disabled=is_busy)
        else:
            st.warning("⚠️ Ollama was not detected on your system. Run `ollama serve` and pull a model first.")
            model = st.text_input("Model Name (Manual)", value="llama3.1", disabled=is_busy)
    else:
        provider = st.selectbox(
            "Provider",
            options=list(models_info["cloud_providers"].keys()) or ["openai", "anthropic", "gemini", "deepseek", "moonshot"],
            format_func=lambda p: {"openai": "OpenAI (GPT)", "anthropic": "Anthropic (Claude)", "gemini": "Google (Gemini)", "deepseek": "DeepSeek (V3/Reasoner)", "moonshot": "Moonshot (Kimi)"}.get(p, p),
            disabled=is_busy,
        )
        model_options = models_info["cloud_providers"].get(provider, [])
        model = st.selectbox("Model", options=model_options, disabled=is_busy) if model_options else st.text_input("Model Name", disabled=is_busy)
        api_key = st.text_input(f"{provider.capitalize()} API Key", type="password", help="Never stored, used only for this request", disabled=is_busy)

        if api_key:
            if st.button("🔑 Verify Key / فحص الاتصال", key="btn_verify_api_key", disabled=is_busy, use_container_width=True, help="Test API key connectivity and retrieve token capacity"):
                try:
                    v_resp = requests.post(
                        f"{BACKEND_URL}/verify-key",
                        json={"provider": provider, "api_key": api_key, "model": model},
                        timeout=10
                    ).json()
                    st.session_state.key_verification = v_resp
                except Exception as e:
                    st.session_state.key_verification = {"status": "error", "message": str(e)}

            v_info = st.session_state.get("key_verification")
            if v_info:
                if v_info.get("status") == "connected":
                    st.success(f"✅ **{v_info.get('provider')} متصل وجاهز!**")
                    st.caption(f"🚀 **سعة السياق (Context Window):** `{v_info.get('context_tokens')}`")
                else:
                    st.error(f"❌ {v_info.get('message')}")
        else:
            st.session_state.pop("key_verification", None)
            st.info("💡 أدخل مفتاح الـ API الخاص بك لتفعيل النماذج السحابية الفائقة.")

    st.divider()
    st.header("Your Documents")

    uploaded_file = st.file_uploader(
        "Upload a Document",
        type=["pdf", "xlsx", "xls", "docx"],
        help="Upload a PDF, Excel (.xlsx/.xls), or Word (.docx) file and start asking questions",
        disabled=is_busy,
    )

    enable_vision = st.checkbox(
        "🖼️ Analyze Charts with Vision AI",
        value=False,
        help="Extracts and describes charts, diagrams, and figures using the selected model.",
        disabled=is_busy,
    )

    if uploaded_file:
        if st.button("Ingest Document", type="primary", use_container_width=True, disabled=is_busy):
            with st.spinner("Reading, chunking, and embedding your document..."):
                form_data = {
                    "enable_vision": "true" if enable_vision else "false",
                    "vision_provider": provider,
                    "vision_model": model if model else "llama3.2-vision",
                    "vision_api_key": api_key if api_key else "",
                }
                # Determine MIME type based on file extension
                ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
                mime_map = {
                    "pdf": "application/pdf",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "xls": "application/vnd.ms-excel",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }
                mime_type = mime_map.get(ext, "application/octet-stream")
                response = requests.post(
                    f"{BACKEND_URL}/ingest",
                    files={"file": (uploaded_file.name, uploaded_file, mime_type)},
                    data=form_data,
                )

            if response.status_code == 200:
                data = response.json()
                fig_msg = f" (including {data.get('figures_analyzed', 0)} charts)" if data.get('figures_analyzed', 0) > 0 else ""
                st.success(f"Done! Added {data['chunks_added']} chunks{fig_msg}")
                st.info(f"Total in database: {data['total_chunks']} chunks")
                st.rerun()
            else:
                st.error("Something went wrong. Is the backend running?")

    # === Knowledge Base — Ingested Documents ===
    st.subheader("📚 Knowledge Base")
    try:
        docs_response = requests.get(f"{BACKEND_URL}/documents", timeout=3)
        docs_data = docs_response.json()
        doc_list = docs_data.get("documents", [])
        if doc_list:
            for doc in doc_list:
                name = doc["name"]
                chunks = doc["chunks"]
                display_name = (name[:27] + "...") if len(name) > 30 else name
                col_doc, col_del = st.columns([5, 1])
                with col_doc:
                    st.markdown(
                        f'<div title="{name}" style="margin-bottom:4px;">'
                        f'📄 <b>{display_name}</b> '
                        f'<span style="color:#888; font-size:0.85em;">— {chunks} chunks</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with col_del:
                    if st.button("🗑️", key=f"del_{name}", disabled=is_busy, help=f"Delete {name}"):
                        st.session_state[f"confirm_del_{name}"] = True

                # Confirmation step to prevent accidental deletion
                if st.session_state.get(f"confirm_del_{name}", False):
                    st.warning(f"Are you sure you want to delete **{display_name}** and all its chunks?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes, delete", key=f"yes_{name}", type="primary", disabled=is_busy):
                            try:
                                del_resp = requests.delete(
                                    f"{BACKEND_URL}/documents/{name}", timeout=10
                                )
                                del_data = del_resp.json()
                                if "error" in del_data:
                                    st.error(del_data["error"])
                                else:
                                    st.success(
                                        f"Deleted **{name}** — {del_data['chunks_removed']} chunks removed. "
                                        f"{del_data['total_remaining']} chunks remaining."
                                    )
                                st.session_state.pop(f"confirm_del_{name}", None)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {e}")
                    with col_no:
                        if st.button("❌ Cancel", key=f"no_{name}", disabled=is_busy):
                            st.session_state.pop(f"confirm_del_{name}", None)
                            st.rerun()
        else:
            st.caption("No documents uploaded yet")
    except Exception:
        st.caption("⚠️ Could not load document list")

    n_results = st.slider(
        "Number of chunks to retrieve",
        min_value=1,
        max_value=10,
        value=3,
        help="How many relevant chunks to fetch from the database per question",
        disabled=is_busy,
    )

    st.divider()

    try:
        status = requests.get(f"{BACKEND_URL}/").json()
        st.metric("Chunks in Database", status["total_chunks"])
    except Exception:
        st.error("Backend is not reachable")

st.divider()

tab_chat, tab_compare = st.tabs([
    "💬 Chat with PDFs / المحادثة والاستفسار",
    "⚖️ Policy Gap Analysis (ITU 2.0) / تحليل الفجوات والمقارنة"
])

with tab_chat:
    # Render chat messages with individual Reply buttons
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            # Display quote banner if this message replied to a specific prior message
            if msg.get("quoted_message"):
                q_txt = msg["quoted_message"]
                q_class = "arabic-quote" if is_arabic(q_txt) else "english-quote"
                q_label = "رد على:" if is_arabic(q_txt) else "Replying to:"
                st.markdown(
                    f'<div class="{q_class}">'
                    f'↩️ <b>{q_label}</b> "{q_txt[:100]}..."'
                    f'</div>',
                    unsafe_allow_html=True
                )

            col_text, col_reply = st.columns([12, 1])
            with col_text:
                render_content_with_mermaid(msg["content"], key_prefix=f"hist_{idx}")
            with col_reply:
                if st.button("↩️", key=f"rep_btn_{idx}", disabled=is_busy, help="Reply specifically to this message"):
                    st.session_state.reply_target = msg["content"]
                    st.rerun()

            if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
                with st.expander("View retrieved chunks", expanded=False):
                    for source in msg["sources"]:
                        ctype = source.get("content_type", "text")
                        if ctype == "table":
                            icon, badge = "📊", " *(Table)*"
                        elif ctype == "figure":
                            icon, badge = "📈", " *(Chart/Figure)*"
                        else:
                            icon, badge = "📄", ""
                        st.markdown(
                            f"{icon} **{source['source']}** — Page {source['page']}{badge} "
                            f"*(similarity: {source['score']}%)*"
                        )

    # Active Reply Target Preview Banner
    if st.session_state.reply_target and not is_busy:
        rep_txt = st.session_state.reply_target
        col_rep_box, col_rep_close = st.columns([11, 1])
        with col_rep_box:
            if is_arabic(rep_txt):
                st.info(f"↩️ **رد على:** \"{rep_txt[:140]}...\"")
            else:
                st.info(f"↩️ **Replying to:** \"{rep_txt[:140]}...\"")
        with col_rep_close:
            if st.button("✖", key="cancel_reply_target_btn", help="Cancel reply"):
                st.session_state.reply_target = None
                st.rerun()

    # Execute pending generation atomically with total isolation
    if st.session_state.pending_turn:
        turn_info = st.session_state.pending_turn
        q_text = turn_info["question"]
        q_quoted = turn_info["quoted_msg"]

        # Capture sliding window of prior conversation turns
        history_payload = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-8:]
        ]

        with st.chat_message("user"):
            if q_quoted:
                q_class = "arabic-quote" if is_arabic(q_quoted) else "english-quote"
                q_label = "رد على:" if is_arabic(q_quoted) else "Replying to:"
                st.markdown(
                    f'<div class="{q_class}">'
                    f'↩️ <b>{q_label}</b> "{q_quoted[:100]}..."'
                    f'</div>',
                    unsafe_allow_html=True
                )
            if is_arabic(q_text):
                st.markdown(f'<div class="arabic-rtl">\n\n{q_text}\n\n</div>', unsafe_allow_html=True)
            else:
                st.write(q_text)

        with st.chat_message("assistant"):
            with st.spinner("Searching your documents... / جاري البحث وتحليل المستندات..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/ask",
                        json={
                            "question": q_text,
                            "n_results": n_results,
                            "provider": provider,
                            "model": model,
                            "api_key": api_key,
                            "history": history_payload,
                            "session_id": st.session_state.current_session_id,
                            "quoted_message": q_quoted,
                        },
                        timeout=120,
                    )
                    data = response.json()

                    if "error" in data:
                        answer = f"⚠️ {data['error']}"
                        sources = []
                    else:
                        answer = data["answer"]
                        sources = data.get("sources", [])

                except Exception as e:
                    answer = f"⚠️ Could not reach backend: {e}"
                    sources = []

                render_content_with_mermaid(answer, key_prefix="live_pending_answer")

                if sources:
                    with st.expander("View retrieved chunks", expanded=False):
                        for source in sources:
                            ctype = source.get("content_type", "text")
                            if ctype == "table":
                                icon, badge = "📊", " *(Table)*"
                            elif ctype == "figure":
                                icon, badge = "📈", " *(Chart/Figure)*"
                            else:
                                icon, badge = "📄", ""
                            st.markdown(
                                f"{icon} **{source['source']}** — Page {source['page']}{badge} "
                                f"*(similarity: {source['score']}%)*"
                            )

        # Commit both messages atomically to session history
        st.session_state.messages.append({
            "role": "user",
            "content": q_text,
            "quoted_message": q_quoted,
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        st.session_state.pending_turn = None
        st.rerun()

with tab_compare:
    st.header("⚖️ ITU AI Readiness 2.0 — Policy Gap Analysis")
    st.caption("Compare two strategic or policy documents and produce a structured gap analysis mapped to the 13 official ITU dimensions and ITU-T Y.3172 pipeline nodes.")

    try:
        docs_res = requests.get(f"{BACKEND_URL}/documents", timeout=3).json()
        available_docs = [d["name"] for d in docs_res.get("documents", [])]
    except Exception:
        available_docs = []

    if len(available_docs) < 2:
        st.warning("⚠️ Please upload at least 2 documents (PDF, Excel, or Word) in the sidebar to perform Policy Gap Analysis.")
    else:
        col_doc_a, col_doc_b = st.columns(2)
        with col_doc_a:
            selected_doc_a = st.selectbox("📄 Document A (المستند الأول)", options=available_docs, index=0, key="sel_cmp_doc_a", disabled=is_busy)
        with col_doc_b:
            selected_doc_b = st.selectbox("📄 Document B (المستند الثاني)", options=available_docs, index=1 if len(available_docs) > 1 else 0, key="sel_cmp_doc_b", disabled=is_busy)

        if selected_doc_a == selected_doc_b:
            st.error("⚠️ Please select two different documents to compare.")

        if st.button("🚀 Run ITU Gap Analysis / بدء تحليل الفجوات", type="primary", use_container_width=True, disabled=is_busy or (selected_doc_a == selected_doc_b)):
            with st.spinner("Analyzing documents against ITU AI Readiness 2.0 dimensions... / جاري مقارنة المستندات وتصنيف الفجوات..."):
                try:
                    comp_resp = requests.post(
                        f"{BACKEND_URL}/compare",
                        json={
                            "doc_a": selected_doc_a,
                            "doc_b": selected_doc_b,
                            "provider": provider,
                            "model": model,
                            "api_key": api_key,
                        },
                        timeout=600,
                    ).json()

                    if "error" in comp_resp:
                        st.error(comp_resp["error"])
                    else:
                        st.session_state.last_comparison = comp_resp
                        st.rerun()
                except Exception as e:
                    st.error(f"Comparison request failed: {e}")

        if "last_comparison" in st.session_state and st.session_state.last_comparison:
            c_data = st.session_state.last_comparison
            st.divider()
            st.subheader(f"📊 Results: `{c_data.get('doc_a')}` vs `{c_data.get('doc_b')}`")
            analysis_text = c_data.get("analysis", "")
            render_content_with_mermaid(analysis_text, key_prefix="compare_result")

            # Clean and sanitize filenames for safe OS download across Windows, Linux, and Mac
            clean_name_a = re.sub(r'[^a-zA-Z0-9_-]', '_', str(c_data.get('doc_a', 'DocA')).rsplit('.', 1)[0])[:25]
            clean_name_b = re.sub(r'[^a-zA-Z0-9_-]', '_', str(c_data.get('doc_b', 'DocB')).rsplit('.', 1)[0])[:25]
            export_filename = f"ITU_Gap_Analysis_{clean_name_a}_vs_{clean_name_b}.pdf"
            
            markdown_content = (
                f"# ITU AI Readiness 2.0 — Policy Gap Analysis\n\n"
                f"- **Document A:** {c_data.get('doc_a')}\n"
                f"- **Document B:** {c_data.get('doc_b')}\n\n---\n\n"
                f"{analysis_text}\n"
            )

            # Generate PDF report
            try:
                pdf_bytes = generate_gap_analysis_pdf(
                    doc_a=c_data.get('doc_a', ''),
                    doc_b=c_data.get('doc_b', ''),
                    analysis_text=analysis_text,
                )
                pdf_ready = True
            except Exception as pdf_err:
                pdf_ready = False
                st.warning(f"PDF generation failed: {pdf_err}. Falling back to Markdown.")

            col_down, col_clear = st.columns([4, 1])
            with col_down:
                if pdf_ready:
                    import base64
                    b64 = base64.b64encode(pdf_bytes).decode()
                    btn_html = f'''
                    <a href="data:application/pdf;base64,{b64}" download="{export_filename}"
                       style="display: inline-block; width: 100%; text-align: center; padding: 0.5rem 1rem;
                              color: white; background-color: #ff4b4b; border-radius: 0.5rem;
                              text-decoration: none; font-weight: 500; font-family: sans-serif;
                              box-sizing: border-box; font-size: 1rem;">
                       📥 Download Gap Analysis / تحميل تقرير الفجوات (PDF)
                    </a>
                    <div style="height: 15px;"></div>
                    '''
                    st.markdown(btn_html, unsafe_allow_html=True)
                else:
                    # Fallback to Markdown if PDF generation failed
                    md_filename = export_filename.replace(".pdf", ".md")
                    st.download_button(
                        label="📥 Download Gap Analysis (Markdown fallback)",
                        data=markdown_content.encode("utf-8"),
                        file_name=md_filename,
                        mime="text/markdown",
                        key="btn_download_gap_analysis",
                        use_container_width=True
                    )
            with col_clear:
                if st.button("🗑️ Clear Results", key="btn_clear_comp_results", help="Clear current comparison results", use_container_width=True):
                    st.session_state.pop("last_comparison", None)
                    st.rerun()

            with st.expander("📋 View Raw Markdown / نسخ كود التقرير", expanded=False):
                st.code(markdown_content, language="markdown")

# Capture new input when not busy
if question := st.chat_input("Ask anything about your documents / اسأل أي سؤال عن مستنداتك", disabled=is_busy):
    st.session_state.pending_turn = {
        "question": question,
        "quoted_msg": st.session_state.reply_target,
    }
    st.session_state.reply_target = None
    st.rerun()
