import streamlit as st
import locale
from datetime import datetime, timedelta, date
from fpdf import FPDF
from translations import TRANSLATIONS

DATE_FMT = "%d.%m.%y"


def detect_language():
    try:
        loc = locale.getdefaultlocale()[0] or ""
    except Exception:
        loc = ""
    lang_code = loc[:2].lower()
    if lang_code in TRANSLATIONS:
        return lang_code
    return "en"


def t(key):
    return TRANSLATIONS[st.session_state.get("lang", "en")].get(key, key)


# --- Recommendation logic via translation keys ---
REC_KEYS = {
    ("Solid", "Single", "size_lt6", "low"):   "rec_no_followup",
    ("Solid", "Single", "size_lt6", "high"):  "rec_solid_single_lt6_high",
    ("Solid", "Multiple", "size_lt6", "low"):  "rec_no_followup",
    ("Solid", "Multiple", "size_lt6", "high"): "rec_solid_multi_lt6_high",
    ("Solid", "Single", "size_6_8", "low"):    "rec_solid_single_68_low",
    ("Solid", "Single", "size_6_8", "high"):   "rec_solid_single_68_high",
    ("Solid", "Multiple", "size_6_8", "low"):  "rec_solid_multi_68_low",
    ("Solid", "Multiple", "size_6_8", "high"): "rec_solid_multi_68_high",
    ("Solid", "Single", "size_gt8", "low"):    "rec_solid_single_gt8",
    ("Solid", "Single", "size_gt8", "high"):   "rec_solid_single_gt8",
    ("Solid", "Multiple", "size_gt8", "low"):  "rec_solid_multi_gt8_low",
    ("Solid", "Multiple", "size_gt8", "high"): "rec_solid_multi_gt8_high",
    ("Subsolid", "Single", "size_gg_lt6", None):  "rec_no_followup",
    ("Subsolid", "Single", "size_gg_gte6", None): "rec_sub_gg_gte6",
    ("Subsolid", "Single", "size_ps_lt6", None):  "rec_no_followup",
    ("Subsolid", "Single", "size_ps_gte6", None): "rec_sub_ps_gte6",
    ("Subsolid", "Multiple", "size_sub_lt6", None):  "rec_sub_multi_lt6",
    ("Subsolid", "Multiple", "size_sub_gte6", None): "rec_sub_multi_gte6",
}

FOLLOW_UP_MONTHS = {
    ("Solid", "Single", "size_lt6", "low"):   [],
    ("Solid", "Single", "size_lt6", "high"):  [12],
    ("Solid", "Multiple", "size_lt6", "low"):  [],
    ("Solid", "Multiple", "size_lt6", "high"): [12],
    ("Solid", "Single", "size_6_8", "low"):    [6, 12, 18, 24],
    ("Solid", "Single", "size_6_8", "high"):   [6, 12, 18, 24],
    ("Solid", "Multiple", "size_6_8", "low"):  [3, 6, 18, 24],
    ("Solid", "Multiple", "size_6_8", "high"): [3, 6, 18, 24],
    ("Solid", "Single", "size_gt8", "low"):    [3],
    ("Solid", "Single", "size_gt8", "high"):   [3],
    ("Solid", "Multiple", "size_gt8", "low"):  [3, 6, 18, 24],
    ("Solid", "Multiple", "size_gt8", "high"): [3, 6, 18, 24],
    ("Subsolid", "Single", "size_gg_lt6", None):  [],
    ("Subsolid", "Single", "size_gg_gte6", None): [6, 12, 24, 36, 48, 60],
    ("Subsolid", "Single", "size_ps_lt6", None):  [],
    ("Subsolid", "Single", "size_ps_gte6", None): [3, 6, 12, 24, 36, 48, 60],
    ("Subsolid", "Multiple", "size_sub_lt6", None):  [3, 6, 24, 48],
    ("Subsolid", "Multiple", "size_sub_gte6", None): [3, 6],
}

SOLID_SIZE_KEYS = ["size_lt6", "size_6_8", "size_gt8"]
SUBSOLID_SINGLE_SIZE_KEYS = ["size_gg_lt6", "size_gg_gte6", "size_ps_lt6", "size_ps_gte6"]
SUBSOLID_MULTI_SIZE_KEYS = ["size_sub_lt6", "size_sub_gte6"]


def sanitize(text):
    return (text
            .replace("\u00b3", "3")
            .replace("\u2265", ">=")
            .replace("\u2192", "->")
            .replace("\u2264", "<="))


def _find_unicode_font():
    """Find a Unicode-capable font on the system. Returns (regular, bold, italic) or None."""
    font_sets = [
        # Windows
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/ariali.ttf"),
        ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeuii.ttf"),
        # Linux (Streamlit Cloud with packages.txt)
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"),
    ]
    import os
    for regular, bold, italic in font_sets:
        if os.path.isfile(regular) and os.path.isfile(bold) and os.path.isfile(italic):
            return (regular, bold, italic)
    # Fallback: try regular only (use it for all styles)
    for regular, bold, italic in font_sets:
        if os.path.isfile(regular):
            return (regular, regular, regular)
    return None


def generate_pdf(data, lang):
    tr = TRANSLATIONS[lang]

    pdf = FPDF()
    pdf.add_page()

    # Add Unicode font for Turkish character support
    font_files = _find_unicode_font()
    if font_files:
        regular, bold, italic = font_files
        pdf.add_font("UniFont", "", regular, uni=True)
        pdf.add_font("UniFont", "B", bold, uni=True)
        pdf.add_font("UniFont", "I", italic, uni=True)
        fn = "UniFont"
    else:
        fn = "Helvetica"
        # Sanitize all Turkish chars for Helvetica (no Unicode support)
        tr = {k: sanitize(v) for k, v in tr.items()}
        data = {k: sanitize(v) if isinstance(v, str) else v for k, v in data.items()}

    pw = pdf.w - pdf.l_margin - pdf.r_margin

    # Title bar
    pdf.set_fill_color(43, 87, 151)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(fn, "B", 18)
    pdf.cell(pw, 14, tr["report_title"], align="C", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "I", 9)
    pdf.cell(pw, 8, tr["page_subtitle"], align="C", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Report date
    pdf.set_text_color(100, 100, 100)
    pdf.set_font(fn, "I", 9)
    pdf.cell(pw, 6, f"{tr['report_generated']}: {datetime.now().strftime(DATE_FMT)}",
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Patient summary
    pdf.set_fill_color(214, 228, 245)
    pdf.set_text_color(43, 87, 151)
    pdf.set_font(fn, "B", 12)
    pdf.cell(pw, 9, f"  {tr['patient_summary']}", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    fields = [
        (tr["name_label"], data["name"]),
        (tr["imaging_date_label"], data["imaging_date"]),
        (tr["nodule_label"], f"{data['nodule_type']}  |  {data['count_display']}  |  {data['size_display']}"),
    ]
    if data["risk_display"]:
        fields.append((tr["risk_label"], data["risk_display"]))

    for label, value in fields:
        pdf.set_font(fn, "B", 10)
        pdf.cell(45, 7, f"  {label}:", new_x="END")
        pdf.set_font(fn, "", 10)
        pdf.cell(0, 7, f"  {sanitize(value)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # Recommendation
    pdf.set_fill_color(214, 228, 245)
    pdf.set_text_color(43, 87, 151)
    pdf.set_font(fn, "B", 12)
    pdf.cell(pw, 9, f"  {tr['recommendation']}", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font(fn, "", 11)
    pdf.multi_cell(pw, 7, f"  {sanitize(data['recommendation'])}")

    if data["is_multiple"]:
        pdf.ln(2)
        pdf.set_text_color(184, 92, 0)
        pdf.set_font(fn, "I", 9)
        note = tr["multiple_note"].replace("**Note:**", "Note:").replace("**Not:**", "Not:")
        pdf.multi_cell(pw, 6, f"  {sanitize(note)}")

    pdf.ln(6)

    # Follow-up
    pdf.set_fill_color(214, 228, 245)
    pdf.set_text_color(43, 87, 151)
    pdf.set_font(fn, "B", 12)
    pdf.cell(pw, 9, f"  {tr['follow_up_schedule']}", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_text_color(30, 30, 30)
    if data["follow_ups"]:
        pdf.set_font(fn, "B", 10)
        pdf.set_fill_color(240, 244, 248)
        pdf.cell(pw / 2, 8, f"    {tr['timeframe']}", fill=True, new_x="END")
        pdf.cell(pw / 2, 8, f"  {tr['suggested_date']}", fill=True,
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_font(fn, "", 10)
        for i, (m, d) in enumerate(data["follow_ups"]):
            if i % 2 == 0:
                pdf.set_fill_color(250, 250, 252)
            else:
                pdf.set_fill_color(240, 244, 248)
            pdf.cell(pw / 2, 7, f"    {m} {tr['months']}", fill=True, new_x="END")
            pdf.cell(pw / 2, 7, f"  {d}", fill=True, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font(fn, "", 11)
        pdf.cell(pw, 7, f"  {tr['no_follow_up']}", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(12)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pw, pdf.get_y())
    pdf.ln(3)
    pdf.set_text_color(150, 150, 150)
    pdf.set_font(fn, "I", 8)
    pdf.cell(pw, 5, tr["pdf_footer"], align="C")

    return bytes(pdf.output())


def main():
    st.set_page_config(page_title="Nodule Follow-Up", layout="centered",
                       initial_sidebar_state="collapsed")

    # Custom CSS
    st.markdown("""
    <style>
    .block-container { padding-top: 1rem; max-width: 800px; }
    div[data-testid="stExpander"] { border: 1px solid #d0d8e4; border-radius: 6px; }
    .header-banner {
        background: #2b5797; color: white; padding: 1.2rem 1.5rem 0.8rem;
        border-radius: 8px; margin-bottom: 1.5rem;
    }
    .header-banner h1 { color: white; font-size: 1.6rem; margin: 0 0 0.2rem; }
    .header-banner p { color: #b0c8e8; font-style: italic; margin: 0; font-size: 0.9rem; }
    .result-box {
        background: #f8fafc; border: 1px solid #d0d8e4; border-radius: 8px;
        padding: 1.2rem; margin-top: 0.5rem; color: #1a2a3a;
    }
    .result-box b, .result-box p { color: #1a2a3a; }
    .result-box h4 { color: #2b5797; margin: 0.8rem 0 0.3rem; }
    .result-box h4:first-child { margin-top: 0; }
    .fu-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
    .fu-table th {
        background: #d6e4f5; color: #2b5797; text-align: left;
        padding: 6px 12px; font-size: 0.9rem;
    }
    .fu-table td { padding: 5px 12px; font-size: 0.9rem; }
    .fu-table tr:nth-child(even) { background: #f0f4f8; }
    .fu-table .date { color: #2b7a3e; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

    # --- Language selector ---
    if "lang" not in st.session_state:
        st.session_state.lang = detect_language()

    lang_options = {"en": "English", "tr": "T\u00fcrk\u00e7e"}

    # --- Header with language selector ---
    hdr_left, hdr_right = st.columns([5, 1])
    with hdr_left:
        st.markdown(f"""
        <div class="header-banner">
            <h1>{t('page_title')}</h1>
            <p>{t('page_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
    with hdr_right:
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        selected_lang = st.selectbox(
            t("language"), options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(st.session_state.lang),
        )
        st.session_state.lang = selected_lang

    # --- Patient Info ---
    st.subheader(t("patient_info"))
    col1, col2 = st.columns(2)
    with col1:
        patient_name = st.text_input(t("patient_name"), key="patient_name_input")
    with col2:
        imaging_date = st.date_input(t("imaging_date"), value=date.today(),
                                      format="DD.MM.YYYY", key="imaging_date_input")

    # --- Classification ---
    st.subheader(t("nodule_classification"))
    col1, col2 = st.columns(2)
    with col1:
        nodule_type = st.radio(t("type"), ["Solid", "Subsolid"],
                               format_func=lambda x: t(x.lower()),
                               horizontal=True, key="nodule_type_input")
    with col2:
        count = st.radio(t("count"), ["Single", "Multiple"],
                         format_func=lambda x: t(x.lower()),
                         horizontal=True, key="count_input")

    # --- Size ---
    size_col, info_col = st.columns([5, 1])
    with size_col:
        st.subheader(t("nodule_size"))
    with info_col:
        show_info = st.button("\u2139\ufe0f", help=t("measurement_info"), key="info_btn")

    if show_info:
        _show_measurement_dialog()

    if nodule_type == "Solid":
        size_keys = SOLID_SIZE_KEYS
    elif count == "Single":
        size_keys = SUBSOLID_SINGLE_SIZE_KEYS
    else:
        size_keys = SUBSOLID_MULTI_SIZE_KEYS

    size_key = st.radio(
        t("select_size"),
        size_keys,
        format_func=lambda x: t(x),
        key=f"size_{nodule_type}_{count}",
        label_visibility="collapsed",
    )

    # --- Risk ---
    risk_raw = None
    if nodule_type == "Solid":
        st.subheader(t("risk_level"))
        risk_raw = st.radio(
            t("select_risk"),
            ["low", "high"],
            format_func=lambda x: t(f"{x}_risk"),
            horizontal=True,
            key="risk_input",
            label_visibility="collapsed",
        )
        with st.expander(t("risk_level") + " - Info", expanded=False):
            st.markdown(t("high_risk_desc"))
            st.markdown(t("low_risk_desc"))
            st.markdown(t("risk_note"))

    # --- Recommendation ---
    st.divider()
    st.subheader(t("recommendation"))

    if not patient_name:
        st.info(t("fill_all_fields"))
    else:
        key = (nodule_type, count, size_key, risk_raw)
        rec_key = REC_KEYS.get(key)
        months = FOLLOW_UP_MONTHS.get(key, [])

        if rec_key:
            rec_text = t(rec_key)
            img_date = datetime.combine(imaging_date, datetime.min.time())

            follow_ups = []
            for m in months:
                fu_date = img_date + timedelta(days=30 * m)
                follow_ups.append((m, fu_date.strftime(DATE_FMT)))

            count_display = t(count.lower())
            size_display = t(size_key)
            risk_display = t(f"{risk_raw}_risk") if risk_raw else ""

            # Build result HTML
            html = '<div class="result-box">'
            html += f'<h4>{t("patient_summary")}</h4>'
            html += f'<b>{t("name_label")}:</b> {patient_name}<br>'
            html += f'<b>{t("imaging_date_label")}:</b> {img_date.strftime(DATE_FMT)}<br>'
            html += f'<b>{t("nodule_label")}:</b> {t(nodule_type.lower())} | {count_display} | {size_display}<br>'
            if risk_display:
                html += f'<b>{t("risk_label")}:</b> {risk_display}<br>'

            html += f'<h4>{t("recommendation")}</h4>'
            html += f'<p>{rec_text}</p>'

            if count == "Multiple":
                note = t("multiple_note").replace("**", "")
                html += f'<p style="color:#b85c00;font-style:italic;">{note}</p>'

            html += f'<h4>{t("follow_up_schedule")}</h4>'
            if follow_ups:
                html += '<table class="fu-table"><tr>'
                html += f'<th>{t("timeframe")}</th><th>{t("suggested_date")}</th></tr>'
                for m, d in follow_ups:
                    html += f'<tr><td>{m} {t("months")}</td><td class="date">{d}</td></tr>'
                html += '</table>'
            else:
                html += f'<p>{t("no_follow_up")}</p>'

            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            # --- PDF Button ---
            st.markdown("")
            data = {
                "name": patient_name,
                "imaging_date": img_date.strftime(DATE_FMT),
                "nodule_type": t(nodule_type.lower()),
                "count_display": count_display,
                "size_display": size_display,
                "risk_display": risk_display,
                "recommendation": rec_text,
                "is_multiple": count == "Multiple",
                "follow_ups": follow_ups,
            }
            pdf_bytes = generate_pdf(data, st.session_state.lang)
            file_name = f"Nodule_Report_{patient_name.replace(' ', '_')}_{datetime.now().strftime('%d%m%y')}.pdf"
            st.download_button(
                label=t("create_report"),
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )


@st.dialog("Measurement Guidelines", width="large")
def _show_measurement_dialog():
    sections = [
        ("info_image_production", ["info_img_1", "info_img_2", "info_img_3", "info_img_4", "info_img_5"]),
        ("info_description", ["info_desc_1", "info_desc_2", "info_desc_3", "info_desc_4"]),
        ("info_partsolid", ["info_ps_1", "info_ps_2"]),
        ("info_general", ["info_gen_1", "info_gen_2", "info_gen_3", "info_gen_4", "info_gen_5"]),
    ]
    for section_key, bullet_keys in sections:
        st.markdown(f"#### {t(section_key)}")
        for bk in bullet_keys:
            st.markdown(f"- {t(bk)}")
        st.markdown("")


if __name__ == "__main__":
    main()
