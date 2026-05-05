import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import io
from datetime import datetime

# ── Page config (must be the very first st.* call) ────────────────────────────
st.set_page_config(page_title="Proposal Go / No-Go", layout="wide", page_icon="📋")

# ── Secrets ───────────────────────────────────────────────────────────────────
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    APP_PASSWORD = "betastream"

try:
    BETA_EMAIL = st.secrets["BETA_EMAIL"]
except Exception:
    BETA_EMAIL = "hello@navisignal.app"

# ── Init auth state ───────────────────────────────────────────────────────────
if "authed" not in st.session_state:
    st.session_state.authed = False

# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authed:
    st.markdown("""
    <style>
      body, .stApp { background-color: #09090b; }
      .stButton > button {
        background: #3b82f6 !important; color: #fff !important; font-weight: 700;
        border: none; border-radius: 6px; font-size: 15px;
      }
      .stButton > button:hover { background: #2563eb !important; }
      .stTextInput > div > div > input {
        background: #18181b; border: 1px solid #3f3f46;
        color: #fafafa; border-radius: 6px; padding: 10px 14px;
      }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:8vh;"></div>', unsafe_allow_html=True)

    _, pw_col, _ = st.columns([1, 2.2, 1])

    with pw_col:
        st.markdown("""
        <div style="background:#111113;border:1px solid #27272a;border-radius:10px;
                    padding:40px 36px 28px;text-align:center;">
          <div style="margin-bottom:20px;">
            <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="22" cy="22" r="20" stroke="#3b82f6" stroke-width="2" opacity="0.3"/>
              <circle cx="22" cy="22" r="3" fill="#3b82f6"/>
              <line x1="22" y1="2" x2="22" y2="10" stroke="#c9a84c" stroke-width="2" stroke-linecap="round"/>
              <line x1="22" y1="34" x2="22" y2="42" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
              <line x1="2" y1="22" x2="10" y2="22" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
              <line x1="34" y1="22" x2="42" y2="22" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            </svg>
          </div>
          <div style="font-family:'DM Serif Display',Georgia,serif;font-size:24px;
                      color:#fafafa;margin-bottom:6px;">
            Supplier Readiness
          </div>
          <div style="font-size:12px;color:#71717a;line-height:1.6;margin-bottom:28px;">
            CSRD-aligned diagnostic for SME and supply chain suppliers<br>
            <em>Beta access only</em>
          </div>
        </div>
        """, unsafe_allow_html=True)

        pwd = st.text_input(
            "",
            type="password",
            placeholder="Enter access password…",
            label_visibility="collapsed",
        )

        if st.button("Enter →", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authed = True
                st.rerun()
            else:
                st.error("Incorrect password. Contact your administrator.")

        st.markdown(
            f"""
            <div style="text-align:center;margin-top:16px;font-size:12px;color:#71717a;">
              <a href="mailto:{BETA_EMAIL}?subject=Beta access request"
                 style="color:#3b82f6;font-weight:600;text-decoration:none;">
                Request beta access
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()

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

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="border-bottom:1px solid #27272a;padding:14px 0 14px;
            display:flex;align-items:center;justify-content:space-between;
            margin-bottom:4px;">
  <div style="font-family:'DM Serif Display',Georgia,serif;font-size:18px;color:#fafafa;">
    Navisignal
    <span style="font-family:'DM Sans',sans-serif;font-size:10px;font-weight:600;
                 letter-spacing:0.1em;text-transform:uppercase;color:#c9a84c;
                 border:1px solid #c9a84c;border-radius:9999px;
                 padding:2px 8px;margin-left:8px;">Beta</span>
  </div>
  <div style="text-align:right;">
    <div style="font-family:'DM Serif Display',Georgia,serif;font-size:15px;color:#fafafa;">Proposal Go / No-Go</div>
    <div style="font-size:11px;color:#71717a;margin-top:1px;">For International Development &amp; Humanitarian Practitioners</div>
  </div>
</div>
""", unsafe_allow_html=True)

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
