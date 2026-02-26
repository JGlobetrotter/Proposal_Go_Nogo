import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import io
from datetime import datetime

# experiment


import streamlit as st
import os
import sys

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Proposal Go / No Go Tool",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: #f4f1ec;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Password screen */
.password-card {
    background: #fff;
    border-radius: 16px;
    padding: 3rem 2.5rem;
    max-width: 420px;
    margin: 8vh auto 0;
    box-shadow: 0 4px 32px rgba(0,0,0,0.08);
    text-align: center;
}
.password-card h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #1a1a2e;
    margin-bottom: 0.25rem;
}
.password-card p {
    color: #6b7280;
    font-size: 0.92rem;
    margin-bottom: 2rem;
}

/* Section headers */
h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: #1a1a2e !important;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-card {
    flex: 1;
    background: #fff;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.metric-card .label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9ca3af;
    margin-bottom: 0.4rem;
}
.metric-card .value {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #1a1a2e;
    line-height: 1;
}

/* Band badge */
.band-low    { background: #d1fae5; color: #065f46; }
.band-medium { background: #fef3c7; color: #92400e; }
.band-high   { background: #fee2e2; color: #991b1b; }
.band-badge {
    display: inline-block;
    padding: 0.45rem 1.1rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* Tag pills */
.tag-pill {
    display: inline-block;
    background: #e0e7ff;
    color: #3730a3;
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 0.2rem 0.2rem 0.2rem 0;
}

/* Why list */
.why-item {
    background: #fff;
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.93rem;
    color: #374151;
}

/* Assumption box */
.assumption-box {
    background: #fff;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    border: 1px solid #e5e7eb;
    font-size: 0.88rem;
    color: #4b5563;
    margin-top: 0.5rem;
}
.assumption-box li { margin-bottom: 0.4rem; }

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 2rem 0;
}

/* Selectbox label override */
.stSelectbox label {
    font-weight: 500 !important;
    color: #374151 !important;
}

/* Button */
.stButton > button {
    background: #1a1a2e !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
#  PASSWORD GATE
# ════════════════════════════════════════════════
PASSWORD = "betaproposal"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div class="password-card">
        <h1>🌱 Sustainability Supplier Diagnostic </h1>
        <p>Supplier Sustainability Readiness Tool — Beta</p>
    </div>
    """, unsafe_allow_html=True)
    pwd = st.text_input("Enter access password", type="password", label_visibility="collapsed",
                        placeholder="Enter password…")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Enter →", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()


# end of experiment

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Proposal Go / No-Go", layout="wide", page_icon="📋")

# ── Dark + yellow theme ─────────────────────────────────────────────────────
st.markdown("""
<style>
  body, .stApp { background-color: #1a1a1a; color: #e8e8e8; }
  section[data-testid="stSidebar"] { background-color: #222222; }
  .block-container { padding-top: 2rem; }
  .card {
    background: #2a2a2a; border: 1px solid #333; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem;
  }
  .section-title { color: #f5c518; font-size: 1rem; font-weight: 700; margin-bottom: .6rem; }
  .verdict-go     { color: #4caf50; font-size: 2rem; font-weight: 900; }
  .verdict-caution{ color: #f5c518; font-size: 2rem; font-weight: 900; }
  .verdict-nogo   { color: #f44336; font-size: 2rem; font-weight: 900; }
  .score-pct { font-size: 3rem; font-weight: 900; color: #f5c518; }
  label, .stSlider label { color: #aaaaaa !important; }
  h1, h2, h3 { color: #f5c518; }
  .stButton > button {
    background: #f5c518; color: #1a1a1a; font-weight: 700;
    border: none; border-radius: 6px;
  }
  .stButton > button:hover { background: #e6b800; }
</style>
""", unsafe_allow_html=True)

# ── Sections & questions ────────────────────────────────────────────────────
SECTIONS = [
    {
        "key": "strategic_fit", "label": "Strategic Fit", "icon": "◎",
        "questions": [
            "Aligns with our organizational mission?",
            "Builds on existing programs or expertise?",
            "Strengthens key donor relationships?",
            "Advances long-term strategic goals?",
        ],
    },
    {
        "key": "org_capacity", "label": "Organizational Capacity", "icon": "⬡",
        "questions": [
            "Sufficient staff expertise available?",
            "Adequate time to prepare a quality proposal?",
            "Established relationships in target geography?",
            "Past performance on similar grants?",
        ],
    },
    {
        "key": "financial", "label": "Financial Viability", "icon": "◈",
        "questions": [
            "Budget covers full cost of delivery?",
            "Acceptable overhead and indirect rate?",
            "Cash-flow manageable during project?",
            "Reporting requirements are feasible?",
        ],
    },
    {
        "key": "risk", "label": "Risk Assessment", "icon": "△",
        "questions": [
            "Political / security environment is stable?",
            "Low risk of scope creep or mission drift?",
            "Manageable compliance requirements?",
            "Reputational risk is acceptable?",
        ],
    },
]

LABELS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}

# ── Session state ───────────────────────────────────────────────────────────
for sec in SECTIONS:
    for i in range(len(sec["questions"])):
        k = f"{sec['key']}_{i}"
        if k not in st.session_state:
            st.session_state[k] = 3

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("# 📋 Proposal Go / No-Go Assessment")
st.markdown("---")

left, right = st.columns([52, 48])

# ═══════════════════════════════════════════════════════════════════════════
# LEFT PANEL — metadata + scoring
# ═══════════════════════════════════════════════════════════════════════════
with left:
    st.markdown("### Organisation & Proposal Details")
    org       = st.text_input("Organisation",  placeholder="e.g. ACME NGO")
    title     = st.text_input("Proposal title", placeholder="e.g. Clean Water for Rural Communities")
    donor     = st.text_input("Donor / funder", placeholder="e.g. USAID")
    deadline  = st.date_input("Submission deadline", value=None)
    evaluator = st.text_input("Evaluator name",  placeholder="Your name")

    st.markdown("---")
    st.markdown("### Scoring  *(1 = Very Low → 5 = Very High)*")

    for sec in SECTIONS:
        st.markdown(f"<div class='section-title'>{sec['icon']} {sec['label']}</div>",
                    unsafe_allow_html=True)
        for i, q in enumerate(sec["questions"]):
            k = f"{sec['key']}_{i}"
            st.session_state[k] = st.slider(
                q, 1, 5, st.session_state[k],
                key=f"slider_{k}",
                format="%d"
            )
        st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — live results
# ═══════════════════════════════════════════════════════════════════════════
with right:
    # ── Compute scores ──────────────────────────────────────────────────────
    section_scores = {}
    total_points   = 0
    max_points     = 0

    for sec in SECTIONS:
        pts = sum(st.session_state[f"{sec['key']}_{i}"]
                  for i in range(len(sec["questions"])))
        mx  = 5 * len(sec["questions"])
        section_scores[sec["key"]] = {"label": sec["label"], "icon": sec["icon"],
                                       "score": pts, "max": mx,
                                       "pct": round(100 * pts / mx)}
        total_points += pts
        max_points   += mx

    overall_pct = round(100 * total_points / max_points)

    if overall_pct >= 70:
        verdict, css, rec = "GO ✅", "verdict-go", "Strong alignment. Proceed with proposal."
    elif overall_pct >= 50:
        verdict, css, rec = "PROCEED WITH CAUTION ⚠️", "verdict-caution", \
            "Mixed signals. Address weak areas before committing."
    else:
        verdict, css, rec = "NO-GO ❌", "verdict-nogo", \
            "Significant gaps identified. Do not pursue at this time."

    # ── Verdict card ────────────────────────────────────────────────────────
    st.markdown("### Overall Verdict")
    st.markdown(f"<div class='card'>"
                f"<div class='{css}'>{verdict}</div>"
                f"<div class='score-pct'>{overall_pct}%</div>"
                f"<p style='color:#aaaaaa'>{rec}</p>"
                f"</div>", unsafe_allow_html=True)

    # ── Section breakdown ───────────────────────────────────────────────────
    st.markdown("### Section Breakdown")
    for v in section_scores.values():
        bar_w = v["pct"]
        color = "#4caf50" if bar_w >= 70 else ("#f5c518" if bar_w >= 50 else "#f44336")
        st.markdown(
            f"<div class='card'>"
            f"<b>{v['icon']} {v['label']}</b> — {v['pct']}% ({v['score']}/{v['max']})<br>"
            f"<div style='background:#333;border-radius:4px;height:10px;margin-top:6px'>"
            f"<div style='width:{bar_w}%;background:{color};height:10px;border-radius:4px'></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    # ── Summary table ───────────────────────────────────────────────────────
    st.markdown("### Score Summary")
    rows = [["Section", "Score", "%"]]
    for v in section_scores.values():
        rows.append([f"{v['icon']} {v['label']}", f"{v['score']}/{v['max']}", f"{v['pct']}%"])
    rows.append(["**TOTAL**", f"**{total_points}/{max_points}**", f"**{overall_pct}%**"])
    st.table(rows)

    # ── PDF export ──────────────────────────────────────────────────────────
    st.markdown("### Export Report")

    def build_pdf():
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        yellow = colors.HexColor("#f5c518")
        dark   = colors.HexColor("#1a1a1a")
        story  = []

        title_style = ParagraphStyle("T", parent=styles["Title"],
                                     textColor=yellow, backColor=dark,
                                     fontSize=18, spaceAfter=12)
        h2_style    = ParagraphStyle("H2", parent=styles["Heading2"],
                                     textColor=yellow, fontSize=13, spaceAfter=6)
        body_style  = ParagraphStyle("B", parent=styles["Normal"],
                                     textColor=colors.HexColor("#e8e8e8"),
                                     backColor=dark, fontSize=10, spaceAfter=4)

        story.append(Paragraph("Proposal Go / No-Go Assessment Report", title_style))
        story.append(Spacer(1, 0.3*cm))

        meta = [
            ["Organisation:", org or "—"],
            ["Proposal title:", title or "—"],
            ["Donor / funder:", donor or "—"],
            ["Deadline:", str(deadline) if deadline else "—"],
            ["Evaluator:", evaluator or "—"],
            ["Report date:", datetime.today().strftime("%Y-%m-%d")],
        ]
        t = Table(meta, colWidths=[4*cm, 13*cm])
        t.setStyle(TableStyle([
            ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#e8e8e8")),
            ("BACKGROUND", (0,0), (-1,-1), dark),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph(f"Overall Verdict: {verdict}  ({overall_pct}%)", h2_style))
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph("Section Breakdown", h2_style))
        tdata = [["Section", "Score", "%"]]
        for v in section_scores.values():
            tdata.append([f"{v['icon']} {v['label']}", f"{v['score']}/{v['max']}", f"{v['pct']}%"])
        tdata.append(["TOTAL", f"{total_points}/{max_points}", f"{overall_pct}%"])
        bt = Table(tdata, colWidths=[9*cm, 4*cm, 4*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), yellow),
            ("TEXTCOLOR", (0,0), (-1,0), dark),
            ("BACKGROUND", (0,1), (-1,-2), dark),
            ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0,1), (-1,-1), colors.HexColor("#e8e8e8")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#444444")),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [dark, colors.HexColor("#2a2a2a")]),
        ]))
        story.append(bt)

        doc.build(story)
        buf.seek(0)
        return buf

    if st.button("⬇ Download PDF Report"):
        pdf = build_pdf()
        fname = f"GoNoGo_{(org or 'report').replace(' ','_')}_{datetime.today().strftime('%Y%m%d')}.pdf"
        st.download_button("📄 Save PDF", data=pdf, file_name=fname, mime="application/pdf")
