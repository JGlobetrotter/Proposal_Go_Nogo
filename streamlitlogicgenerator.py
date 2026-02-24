"""
app.py  -  Proposal Go/No-Go Diagnostic
Self-contained Streamlit app. All logic is in this one file.

Run locally:
    pip install streamlit reportlab
    streamlit run app.py

Deploy to Streamlit Cloud:
    Push this file (and nothing else) to your repo root.
    Set the main file to app.py in Streamlit Cloud settings.
"""

import io
import streamlit as st
from datetime import date, datetime

# ── ReportLab imports (PDF generation) ────────────────────────────────────────
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import Flowable


# ══════════════════════════════════════════════════════════════════════════════
# SECTION DEFINITIONS  (scoring config)
# ══════════════════════════════════════════════════════════════════════════════
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
        "key": "organizational_capacity", "label": "Organizational Capacity", "icon": "⬡",
        "questions": [
            "Sufficient staff expertise available?",
            "Adequate time to prepare a quality proposal?",
            "Established relationships in target geography?",
            "Past performance on similar grants?",
        ],
    },
    {
        "key": "financial_viability", "label": "Financial Viability", "icon": "◈",
        "questions": [
            "Budget covers full cost of delivery?",
            "Acceptable overhead and indirect rate?",
            "Cash-flow manageable during project?",
            "Reporting requirements are feasible?",
        ],
    },
    {
        "key": "risk_assessment", "label": "Risk Assessment", "icon": "△",
        "questions": [
            "Political / security environment is stable?",
            "Low risk of scope creep or mission drift?",
            "Manageable compliance requirements?",
            "Reputational risk is acceptable?",
        ],
    },
]

SCORE_LABELS = {0: "—", 1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
PASSWORD = "GOproposal"


# ══════════════════════════════════════════════════════════════════════════════
# SCORING LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def compute_decision(sections):
    total     = sum(s["score"]     for s in sections.values())
    max_total = sum(s["max_score"] for s in sections.values())
    pct       = (total / max_total * 100) if max_total else 0
    if pct >= 70:   verdict = "GO"
    elif pct >= 50: verdict = "PROCEED WITH CAUTION"
    else:           verdict = "NO-GO"
    return verdict, total, max_total, pct


def section_label(score, max_score):
    if max_score == 0: return "Weak"
    p = score / max_score * 100
    if p >= 70: return "Strong"
    if p >= 50: return "Moderate"
    return "Weak"


def generate_narrative(verdict, pct, sections, proposal_title="this proposal"):
    key_to_name = {
        "strategic_fit": "Strategic Fit",
        "organizational_capacity": "Organizational Capacity",
        "financial_viability": "Financial Viability",
        "risk_assessment": "Risk Assessment",
    }
    strengths, weaknesses = [], []
    for key, sec in sections.items():
        name = key_to_name.get(key, key.replace("_", " ").title())
        lbl  = section_label(sec["score"], sec["max_score"])
        if lbl == "Strong": strengths.append(name)
        elif lbl == "Weak": weaknesses.append(name)

    def fmt(lst):
        if not lst:       return ""
        if len(lst) == 1: return lst[0]
        return ", ".join(lst[:-1]) + " and " + lst[-1]

    if verdict == "GO":
        summary = (
            f'The proposal "{proposal_title}" achieved {pct:.0f}%, indicating strong '
            f'overall readiness. '
        )
        if strengths:
            summary += f'Clear strengths in {fmt(strengths)} provide a solid foundation. '
        if weaknesses:
            summary += f'Monitor {fmt(weaknesses)} during implementation. '
        summary += 'The risk-adjusted case for proceeding is positive.'
        next_steps = (
            "1. Initiate a proposal kick-off meeting within 5 working days.\n"
            "2. Assign a proposal coordinator and writing schedule.\n"
            "3. Begin partnership outreach and letters-of-support collection.\n"
            "4. Develop a budget framework and confirm cost-share requirements.\n"
            "5. Schedule a pre-submission review with the Programme Director."
        )
    elif verdict == "PROCEED WITH CAUTION":
        summary = (
            f'The proposal "{proposal_title}" achieved {pct:.0f}%, indicating moderate '
            f'readiness. The opportunity warrants consideration but gaps must be addressed. '
        )
        if strengths: summary += f'Key strengths: {fmt(strengths)}. '
        if weaknesses: summary += f'Address gaps in {fmt(weaknesses)} before proceeding. '
        summary += 'A conditional go-ahead is recommended with a clear mitigation plan.'
        next_steps = (
            "1. Convene a risk-review meeting to assess weak-scoring areas.\n"
            "2. Identify whether partnerships can offset capacity shortfalls.\n"
            "3. Obtain senior leadership sign-off before writing begins.\n"
            "4. Develop a risk register as part of the proposal narrative.\n"
            "5. Re-evaluate if additional red flags emerge during preparation."
        )
    else:
        summary = (
            f'The proposal "{proposal_title}" achieved {pct:.0f}%, below the minimum '
            f'threshold. Significant deficiencies suggest unacceptably high delivery risk. '
        )
        if weaknesses: summary += f'Critical weaknesses in {fmt(weaknesses)}. '
        summary += 'Declining preserves capacity for stronger opportunities.'
        next_steps = (
            "1. Communicate the No-Go decision to all internal stakeholders.\n"
            "2. Document lessons learned for future assessments.\n"
            "3. Consider whether a sub-grant role might still be feasible.\n"
            "4. Explore alternative funding that better matches current capacity.\n"
            "5. Use this diagnostic to build a capacity-strengthening plan."
        )
    return summary, next_steps


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION
# ══════════════════════════════════════════════════════════════════════════════
C_PRIMARY   = colors.HexColor("#1e3a5f")
C_ACCENT    = colors.HexColor("#2563eb")
C_MUTED     = colors.HexColor("#6b7280")
C_BORDER    = colors.HexColor("#e5e7eb")
C_ROW_ALT   = colors.HexColor("#f9fafb")
C_HDR       = colors.HexColor("#1e3a5f")
C_WHITE     = colors.white
C_GO_C      = colors.HexColor("#16a34a")
C_GO_BG     = colors.HexColor("#dcfce7")
C_CAU_C     = colors.HexColor("#d97706")
C_CAU_BG    = colors.HexColor("#fef3c7")
C_NOG_C     = colors.HexColor("#dc2626")
C_NOG_BG    = colors.HexColor("#fee2e2")
SEC_COLORS  = {
    "strategic_fit":           colors.HexColor("#7c3aed"),
    "organizational_capacity": colors.HexColor("#0891b2"),
    "financial_viability":     colors.HexColor("#059669"),
    "risk_assessment":         colors.HexColor("#ea580c"),
}
SEC_DISPLAY = {
    "strategic_fit": "Strategic Fit",
    "organizational_capacity": "Organizational Capacity",
    "financial_viability": "Financial Viability",
    "risk_assessment": "Risk Assessment",
}


def _verdict_colors(verdict):
    if verdict == "GO":                   return C_GO_C,  C_GO_BG
    if verdict == "PROCEED WITH CAUTION": return C_CAU_C, C_CAU_BG
    return C_NOG_C, C_NOG_BG


def _verdict_emoji(verdict):
    return {"GO": "GO", "PROCEED WITH CAUTION": "PROCEED WITH CAUTION", "NO-GO": "NO-GO"}.get(verdict, verdict)


class _ScoreBar(Flowable):
    def __init__(self, score, max_score, bar_color, width=3.5*inch, height=8):
        super().__init__()
        self.score = score; self.max_score = max_score
        self.bar_color = bar_color; self.width = width; self.height = height

    def draw(self):
        pct = self.score / self.max_score if self.max_score else 0
        self.canv.setFillColor(C_BORDER)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        if pct > 0:
            self.canv.setFillColor(self.bar_color)
            self.canv.roundRect(0, 0, self.width * pct, self.height, 3, fill=1, stroke=0)

    def wrap(self, *args):
        return self.width, self.height


def _pdf_styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "h1":      s("h1",    fontSize=20, textColor=C_PRIMARY, fontName="Helvetica-Bold",
                              leading=26, alignment=TA_CENTER),
        "sub":     s("sub",   fontSize=11, textColor=C_MUTED, alignment=TA_CENTER),
        "sec_h":   s("sec_h", fontSize=12, textColor=C_PRIMARY, fontName="Helvetica-Bold", spaceAfter=3),
        "lbl":     s("lbl",   fontSize=8,  textColor=C_MUTED, fontName="Helvetica-Bold"),
        "body":    s("body",  fontSize=9.5, textColor=colors.HexColor("#374151"), leading=14),
        "q_text":  s("q_text",fontSize=9,  textColor=colors.HexColor("#374151")),
        "q_score": s("q_score",fontSize=9, textColor=C_PRIMARY, fontName="Helvetica-Bold",
                               alignment=TA_RIGHT),
        "verdict": s("verdict",fontSize=22,fontName="Helvetica-Bold", alignment=TA_CENTER),
        "note":    s("note",  fontSize=9,  textColor=colors.HexColor("#374151"), leading=13, leftIndent=4),
    }


def _hf(canvas, doc):
    canvas.saveState()
    W, H = letter
    canvas.setFillColor(C_HDR)
    canvas.rect(0, H - 34, W, 34, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(0.5*inch, H - 21, "PROPOSAL GO/NO-GO DIAGNOSTIC REPORT")
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(W - 0.5*inch, H - 21, f"Page {doc.page}")
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(0.5*inch, 0.4*inch, W - 0.5*inch, 0.4*inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_MUTED)
    canvas.drawCentredString(W/2, 0.24*inch, "Confidential – For internal use only")
    canvas.restoreState()


def generate_pdf(data):
    """Generate PDF and return bytes."""
    buf = io.BytesIO()
    sections = data["sections"]
    verdict, total, max_total, pct = compute_decision(sections)
    fg, bg = _verdict_colors(verdict)
    st_  = _pdf_styles()

    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.65*inch, bottomMargin=0.65*inch)
    story = []

    # Cover
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(data.get("organization", ""), st_["sub"]))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(data.get("proposal_title", "Untitled Proposal"), st_["h1"]))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        f'Donor: {data.get("donor") or "—"}   |   Deadline: {data.get("deadline") or "—"}',
        st_["sub"]))
    story.append(Spacer(1, 0.35*inch))

    banner = Table([[Paragraph(verdict, ParagraphStyle(
        "vb", parent=st_["verdict"], textColor=fg))]],
        colWidths=[5.5*inch])
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 16), ("BOTTOMPADDING",(0,0),(-1,-1), 16),
        ("LEFTPADDING",   (0,0),(-1,-1), 18), ("RIGHTPADDING", (0,0),(-1,-1), 18),
        ("BOX",           (0,0),(-1,-1), 1.5, fg),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.28*inch))

    # Score summary row
    sd = [
        [Paragraph("TOTAL SCORE", st_["lbl"]), Paragraph("PERCENTAGE", st_["lbl"]),
         Paragraph("EVALUATOR",   st_["lbl"]), Paragraph("DATE", st_["lbl"])],
        [Paragraph(f"<b>{total} / {max_total}</b>",
                   ParagraphStyle("sv", fontSize=16, fontName="Helvetica-Bold",
                                  textColor=C_PRIMARY, alignment=TA_CENTER)),
         Paragraph(f"<b>{pct:.0f}%</b>",
                   ParagraphStyle("sp", fontSize=16, fontName="Helvetica-Bold",
                                  textColor=fg, alignment=TA_CENTER)),
         Paragraph(data.get("evaluator") or "—", st_["body"]),
         Paragraph(data.get("date_evaluated") or "—", st_["body"])],
    ]
    st_table = Table(sd, colWidths=[1.3*inch, 1.3*inch, 2.0*inch, 1.3*inch])
    st_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_HDR), ("TEXTCOLOR",(0,0),(-1,0), C_WHITE),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"), ("VALIGN",(0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
    ]))
    story.append(st_table)
    story += [Spacer(1, 0.28*inch), HRFlowable(width="100%", thickness=0.4, color=C_BORDER), Spacer(1, 0.22*inch)]

    # Analysis
    summary_text, next_steps_text = generate_narrative(
        verdict, pct, sections,
        data.get("proposal_title", "this proposal"))

    story.append(Paragraph("Diagnostic Analysis", st_["sec_h"]))
    story.append(Spacer(1, 5))

    a_rows = [
        [Paragraph("Executive Summary",
                   ParagraphStyle("ah", fontSize=8.5, fontName="Helvetica-Bold", textColor=C_ACCENT))],
        [Paragraph(summary_text, st_["body"])],
        [Spacer(1, 5)],
        [Paragraph("Strategic Next Steps",
                   ParagraphStyle("ah2", fontSize=8.5, fontName="Helvetica-Bold", textColor=C_ACCENT))],
        [Paragraph(next_steps_text.replace("\n", "<br/>"), st_["body"])],
    ]
    if data.get("notes"):
        a_rows += [
            [Spacer(1, 4)],
            [Paragraph("Evaluator Notes",
                       ParagraphStyle("ah3", fontSize=8.5, fontName="Helvetica-Bold", textColor=C_MUTED))],
            [Paragraph(data["notes"], st_["note"])],
        ]
    at = Table(a_rows, colWidths=[6.3*inch])
    at.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,-1), colors.HexColor("#f5f3ff")),
        ("LEFTPADDING", (0,0),(-1,-1), 12), ("RIGHTPADDING",(0,0),(-1,-1), 12),
        ("TOPPADDING",  (0,0),(-1,-1), 7),  ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("BOX",         (0,0),(-1,-1), 1, colors.HexColor("#7c3aed")),
    ]))
    story.append(at)
    story += [Spacer(1, 0.22*inch), HRFlowable(width="100%", thickness=0.4, color=C_BORDER), Spacer(1, 0.22*inch)]

    # Summary table
    story.append(Paragraph("Section Score Summary", st_["sec_h"]))
    story.append(Spacer(1, 5))
    rows = [["Section", "Score", "Max", "%", "Rating"]]
    ts, tm = 0, 0
    for key, sec in sections.items():
        s, m = sec["score"], sec["max_score"]
        ts += s; tm += m
        name = SEC_DISPLAY.get(key, key.replace("_"," ").title())
        rows.append([
            Paragraph(name, st_["q_text"]),
            Paragraph(str(s), st_["q_score"]),
            Paragraph(str(m), st_["q_score"]),
            Paragraph(f"{s/m*100:.0f}%" if m else "—", st_["q_score"]),
            Paragraph(section_label(s, m), st_["q_score"]),
        ])
    rows.append([
        Paragraph("<b>TOTAL</b>", ParagraphStyle("tb", fontSize=9.5, fontName="Helvetica-Bold", textColor=C_PRIMARY)),
        Paragraph(f"<b>{ts}</b>", ParagraphStyle("ts2", fontSize=9.5, fontName="Helvetica-Bold", textColor=C_PRIMARY, alignment=TA_RIGHT)),
        Paragraph(f"<b>{tm}</b>", ParagraphStyle("tm2", fontSize=9.5, fontName="Helvetica-Bold", textColor=C_PRIMARY, alignment=TA_RIGHT)),
        Paragraph(f"<b>{ts/tm*100:.0f}%</b>" if tm else "—",
                  ParagraphStyle("tp2", fontSize=9.5, fontName="Helvetica-Bold", textColor=C_ACCENT, alignment=TA_RIGHT)),
        Paragraph("", st_["q_score"]),
    ])
    n = len(rows)
    t = Table(rows, colWidths=[2.6*inch, 0.7*inch, 0.7*inch, 0.75*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C_HDR), ("TEXTCOLOR",(0,0),(-1,0), C_WHITE),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,0), 8),
        ("ALIGN",         (1,0),(-1,-1), "CENTER"), ("VALIGN",(0,0),(-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,n-2),[C_WHITE, C_ROW_ALT]),
        ("BACKGROUND",    (0,n-1),(-1,n-1), colors.HexColor("#e0e7ff")),
        ("GRID",          (0,0),(-1,-1), 0.35, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6), ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 7), ("RIGHTPADDING", (0,0),(-1,-1), 7),
    ]))
    story.append(t)
    story += [Spacer(1, 0.22*inch), HRFlowable(width="100%", thickness=0.4, color=C_BORDER), Spacer(1, 0.22*inch)]

    # Section detail cards
    story.append(Paragraph("Detailed Section Scores", st_["sec_h"]))
    story.append(Spacer(1, 6))
    for key, sec in sections.items():
        display = SEC_DISPLAY.get(key, key.replace("_"," ").title())
        color   = SEC_COLORS.get(key, C_ACCENT)
        s, m    = sec["score"], sec["max_score"]
        pct_s   = s / m if m else 0
        lbl     = section_label(s, m)

        card = []
        hdr = Table([[
            Paragraph(f'<b>{display}</b>',
                      ParagraphStyle("sh", fontSize=11, fontName="Helvetica-Bold", textColor=C_WHITE)),
            Paragraph(f'<b>{s}/{m}  |  {pct_s*100:.0f}%  |  {lbl}</b>',
                      ParagraphStyle("ss", fontSize=9.5, fontName="Helvetica-Bold",
                                     textColor=C_WHITE, alignment=TA_RIGHT)),
        ]], colWidths=[3.3*inch, 3.0*inch])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), color),
            ("TOPPADDING",    (0,0),(-1,-1), 8), ("BOTTOMPADDING",(0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 11), ("RIGHTPADDING",(0,0),(-1,-1), 11),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        card.append(hdr)
        card.append(_ScoreBar(s, m, color, width=6.3*inch, height=6))
        card.append(Spacer(1, 5))
        if "questions" in sec:
            q_rows = [["Question", "Score", "Max"]]
            for q in sec["questions"]:
                q_rows.append([
                    Paragraph(q["question"], st_["q_text"]),
                    Paragraph(str(q["score"]), st_["q_score"]),
                    Paragraph(str(q["max"]),   st_["q_score"]),
                ])
            qt = Table(q_rows, colWidths=[4.7*inch, 0.8*inch, 0.8*inch])
            qt.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0), C_HDR), ("TEXTCOLOR",(0,0),(-1,0), C_WHITE),
                ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,0), 8),
                ("ALIGN",         (1,0),(-1,-1), "CENTER"), ("VALIGN",(0,0),(-1,-1), "MIDDLE"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_ROW_ALT]),
                ("GRID",          (0,0),(-1,-1), 0.35, C_BORDER),
                ("TOPPADDING",    (0,0),(-1,-1), 5), ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                ("LEFTPADDING",   (0,0),(-1,-1), 7), ("RIGHTPADDING", (0,0),(-1,-1), 7),
            ]))
            card.append(qt)
        card.append(Spacer(1, 0.18*inch))
        story.append(KeepTogether(card))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT APP
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Proposal Go/No-Go Diagnostic",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Shared CSS ─────────────────────────────────────────────────────────────────
SHARED_CSS = """
<style>
  html, body, [data-testid="stAppViewContainer"],
  [data-testid="stMain"], .main {
    background-color: #1a1a1a !important;
    color: #e8e8e8 !important;
  }
  #MainMenu, footer, header, [data-testid="stToolbar"],
  [data-testid="stDecoration"] { display: none !important; }

  /* inputs */
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea {
    background: #2a2a2a !important;
    color: #e8e8e8 !important;
    border: 1px solid #3a3a3a !important;
    border-radius: 5px !important;
  }
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextArea"] textarea:focus {
    border-color: #f5c518 !important;
    box-shadow: none !important;
  }
  [data-testid="stTextInput"] label,
  [data-testid="stTextArea"] label,
  [data-testid="stDateInput"] label,
  [data-testid="stSlider"] label {
    color: #888 !important;
    font-size: 11px !important;
    font-family: monospace !important;
    letter-spacing: 0.08em !important;
  }
  /* date input */
  [data-testid="stDateInput"] input {
    background: #2a2a2a !important;
    color: #e8e8e8 !important;
    border: 1px solid #3a3a3a !important;
    border-radius: 5px !important;
  }
  /* sliders */
  [data-testid="stSlider"] [role="slider"] {
    background: #f5c518 !important;
    border-color: #f5c518 !important;
  }
  /* tabs */
  [data-baseweb="tab-list"] {
    background: #222 !important;
    border-bottom: 1px solid #333 !important;
    gap: 3px;
  }
  [data-baseweb="tab"] {
    background: transparent !important;
    color: #666 !important;
    font-family: monospace !important;
    font-size: 11px !important;
    border: 1px solid transparent !important;
    border-radius: 4px !important;
    padding: 5px 12px !important;
  }
  [aria-selected="true"][data-baseweb="tab"] {
    background: #f5c51820 !important;
    color: #f5c518 !important;
    border-color: #f5c51855 !important;
  }
  [data-baseweb="tab-highlight"],
  [data-baseweb="tab-border"] { display: none !important; }
  /* download button */
  [data-testid="stDownloadButton"] button {
    background: #f5c518 !important;
    color: #1a1a1a !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: monospace !important;
    width: 100% !important;
    border-radius: 5px !important;
    padding: 10px !important;
  }
  [data-testid="stDownloadButton"] button:hover {
    background: #e6b800 !important;
  }
  /* regular buttons */
  [data-testid="stButton"] button {
    background: #f5c518 !important;
    color: #1a1a1a !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: monospace !important;
    border-radius: 5px !important;
    width: 100%;
    padding: 10px !important;
  }
  [data-testid="stButton"] button:hover {
    background: #e6b800 !important;
    border: none !important;
  }
  hr { border-color: #2f2f2f !important; }
</style>
"""
st.markdown(SHARED_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# ══════════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
    <div style="
      background: #222;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 48px 40px 40px;
      width: 380px;
      text-align: center;
    ">
      <div style="
        width: 10px; height: 10px; border-radius: 50%;
        background: #f5c518;
        box-shadow: 0 0 12px #f5c518;
        display: inline-block;
        margin-bottom: 16px;
      "></div>
      <div style="
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 0.2em;
        color: #f5c518;
        text-transform: uppercase;
        margin-bottom: 8px;
      ">Proposal Assessment Tool</div>
      <h1 style="
        font-family: Georgia, serif;
        font-size: 22px;
        font-weight: 400;
        color: #ffffff;
        margin: 0 0 6px;
      ">Go / No-Go Diagnostic</h1>
      <p style="
        font-family: Helvetica, sans-serif;
        font-size: 12px;
        color: #666;
        margin: 0 0 28px;
      ">Enter your access password to continue</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Centre the form
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        pw = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
            label_visibility="collapsed",
        )
        if st.button("Unlock"):
            if pw == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.markdown(
                    "<p style='color:#dc2626;font-family:monospace;font-size:12px;"
                    "text-align:center;margin-top:8px'>Incorrect password. Try again.</p>",
                    unsafe_allow_html=True,
                )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP  (only shown after authentication)
# ══════════════════════════════════════════════════════════════════════════════

# Header bar
st.markdown("""
<div style="
  background: #222;
  border-bottom: 1px solid #2f2f2f;
  padding: 16px 28px 13px;
  margin-bottom: 20px;
">
  <span style="
    display:inline-block; width:7px; height:7px; border-radius:50%;
    background:#f5c518; box-shadow:0 0 8px #f5c51888;
    margin-right:8px; vertical-align:middle;
  "></span>
  <span style="
    font-family:monospace; font-size:9.5px; letter-spacing:0.2em;
    color:#f5c518; text-transform:uppercase; vertical-align:middle;
  ">Proposal Assessment Tool</span>
  <h1 style="
    font-family:Georgia,serif; font-size:21px; font-weight:400;
    color:#fff; margin:4px 0 2px; letter-spacing:-0.01em;
  ">Go / No-Go Diagnostic</h1>
  <p style="
    font-family:Helvetica,sans-serif; font-size:11.5px; color:#aaa; margin:0;
  ">Evaluate proposal readiness across four dimensions</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([52, 48], gap="medium")


# ── LEFT: Intake Form ──────────────────────────────────────────────────────────
with left:
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Proposal Details</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        org   = st.text_input("ORGANISATION",   placeholder="Hope Bridge Foundation",        key="org")
    with c2:
        title = st.text_input("PROPOSAL TITLE", placeholder="Clean Water Access – Kenya",    key="title")
    c3, c4 = st.columns(2)
    with c3:
        donor = st.text_input("DONOR / FUNDER", placeholder="USAID",                         key="donor")
    with c4:
        deadline = st.date_input("SUBMISSION DEADLINE", value=None, format="YYYY-MM-DD",     key="deadline")
    evaluator = st.text_input("EVALUATOR NAME", placeholder="Your name",                     key="evaluator")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Scoring Sections</p>', unsafe_allow_html=True)

    tabs = st.tabs([f"{s['icon']}  {s['label']}" for s in SECTIONS])
    scores = {}
    for tab, sec in zip(tabs, SECTIONS):
        with tab:
            sec_scores = []
            for qi, question in enumerate(sec["questions"]):
                val = st.slider(
                    question,
                    min_value=0, max_value=5, value=0,
                    key=f"s_{sec['key']}_{qi}",
                    help="0 = not scored  |  1 Very Low → 5 Very High",
                )
                sec_scores.append(val)
            scores[sec["key"]] = {
                "score":     sum(sec_scores),
                "max_score": len(sec["questions"]) * 5,
                "questions": [
                    {"question": q, "score": sec_scores[i], "max": 5}
                    for i, q in enumerate(sec["questions"])
                ],
            }

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:6px">Evaluator Notes (optional)</p>', unsafe_allow_html=True)
    notes = st.text_area(
        "notes_label",
        placeholder="Any context, caveats, or observations...",
        label_visibility="collapsed",
        height=85,
        key="notes",
    )


# ── RIGHT: Live Results ────────────────────────────────────────────────────────
with right:
    verdict, total, max_total, pct = compute_decision(scores)
    pct_frac = pct / 100

    verdict_color = "#f5c518" if verdict == "GO" else "#e8e8e8" if verdict == "PROCEED WITH CAUTION" else "#aaaaaa"
    emoji_sym     = "●" if verdict == "GO" else "◐" if verdict == "PROCEED WITH CAUTION" else "○"

    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Live Results</p>', unsafe_allow_html=True)

    # Verdict badge
    bar_w   = pct_frac * 100
    bar_cls = "bar-fill-strong" if pct_frac >= 0.7 else "bar-fill-moderate" if pct_frac >= 0.5 else "bar-fill-weak"
    bar_col = "#f5c518" if pct_frac >= 0.7 else "#f5c51899" if pct_frac >= 0.5 else "#555"

    st.markdown(f"""
    <div style="display:inline-flex;align-items:center;gap:12px;padding:10px 18px;
                border-radius:7px;background:#f5c51818;border:1.5px solid #f5c51850;margin-bottom:10px">
      <span style="font-size:19px;color:{verdict_color};line-height:1">{emoji_sym}</span>
      <div>
        <div style="font-family:Helvetica,sans-serif;font-size:15px;font-weight:700;
                    color:{verdict_color};letter-spacing:0.05em">{verdict}</div>
        <div style="font-family:monospace;font-size:10.5px;color:#777">
          {total} / {max_total} pts &nbsp;·&nbsp; {pct:.0f}%
        </div>
      </div>
    </div>
    <div style="background:#3a3a3a;border-radius:99px;height:4px;overflow:hidden;margin-bottom:16px">
      <div style="width:{bar_w:.1f}%;height:100%;background:{bar_col};border-radius:99px;transition:width .4s"></div>
    </div>
    """, unsafe_allow_html=True)

    # Section breakdown
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Section Breakdown</p>', unsafe_allow_html=True)

    for sec in SECTIONS:
        sd      = scores[sec["key"]]
        s, m    = sd["score"], sd["max_score"]
        sp      = s / m if m else 0
        lbl     = section_label(s, m)
        s_color = "#f5c518" if lbl == "Strong" else "#e8e8e8" if lbl == "Moderate" else "#888"
        b_col   = "#f5c518" if sp >= 0.7 else "#f5c51899" if sp >= 0.5 else "#555"

        st.markdown(f"""
        <div style="background:#2a2a2a;border:1px solid #333;border-radius:7px;
                    padding:10px 13px;margin-bottom:7px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-family:Helvetica,sans-serif;font-size:12px;color:#ddd">
              <span style="color:#555;margin-right:5px">{sec['icon']}</span>{sec['label']}
            </span>
            <span style="display:flex;gap:10px;align-items:center">
              <span style="font-family:monospace;font-size:10.5px;font-weight:600;color:{s_color}">{lbl}</span>
              <span style="font-family:monospace;font-size:10.5px;color:#555">{s}/{m}</span>
            </span>
          </div>
          <div style="background:#3a3a3a;border-radius:99px;height:4px;overflow:hidden">
            <div style="width:{sp*100:.1f}%;height:100%;background:{b_col};border-radius:99px;transition:width .4s"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Recommendation
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Recommendation</p>', unsafe_allow_html=True)
    if pct >= 70:
        reco = "This proposal demonstrates <strong style='color:#f5c518'>strong readiness</strong> across all dimensions. Proceed with full team commitment. Assign a lead writer and schedule kick-off within 5 working days."
    elif pct >= 50:
        reco = "This proposal shows <strong style='color:#e8e8e8'>moderate readiness</strong>. Proceed conditionally — address weak areas before committing full resources. Obtain senior sign-off and develop a risk mitigation plan."
    else:
        reco = "This proposal has <strong style='color:#888'>critical gaps</strong> across multiple dimensions. Declining preserves capacity for stronger opportunities. Document lessons learned and consider a sub-grantee role."

    st.markdown(f"""
    <div style="background:#2a2a2a;border:1px solid #333;border-radius:7px;
                padding:13px 15px;font-family:Helvetica,sans-serif;
                font-size:12.5px;color:#999;line-height:1.65;margin-bottom:16px">
      {reco}
    </div>
    """, unsafe_allow_html=True)

    # Score summary table
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Score Summary</p>', unsafe_allow_html=True)
    rows_html = ""
    for sec in SECTIONS:
        sd   = scores[sec["key"]]
        s, m = sd["score"], sd["max_score"]
        sp   = s / m if m else 0
        c    = "#f5c518" if sp >= 0.7 else "#e8e8e8" if sp >= 0.5 else "#888"
        rows_html += f"""
        <tr>
          <td style="padding:7px 10px;color:#999;border-bottom:1px solid #2f2f2f">{sec['icon']} {sec['label']}</td>
          <td style="padding:7px 10px;color:#ddd;text-align:center;border-bottom:1px solid #2f2f2f">{s}</td>
          <td style="padding:7px 10px;color:#555;text-align:center;border-bottom:1px solid #2f2f2f">{m}</td>
          <td style="padding:7px 10px;color:{c};text-align:center;border-bottom:1px solid #2f2f2f">{sp*100:.0f}%</td>
        </tr>"""

    tc    = "#f5c518" if pct_frac >= 0.7 else "#e8e8e8" if pct_frac >= 0.5 else "#888"
    st.markdown(f"""
    <div style="background:#2a2a2a;border:1px solid #333;border-radius:7px;
                overflow:hidden;margin-bottom:18px">
      <table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:11.5px">
        <thead>
          <tr style="border-bottom:1px solid #2f2f2f">
            <th style="padding:7px 10px;color:#555;font-size:9.5px;font-weight:400;text-align:left">Section</th>
            <th style="padding:7px 10px;color:#555;font-size:9.5px;font-weight:400">Score</th>
            <th style="padding:7px 10px;color:#555;font-size:9.5px;font-weight:400">Max</th>
            <th style="padding:7px 10px;color:#555;font-size:9.5px;font-weight:400">%</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
          <tr style="background:#f5c51818;border-top:1px solid #3a3a3a">
            <td style="padding:8px 10px;color:#fff;font-weight:700">TOTAL</td>
            <td style="padding:8px 10px;color:{tc};font-weight:700;text-align:center">{total}</td>
            <td style="padding:8px 10px;color:#555;text-align:center">{max_total}</td>
            <td style="padding:8px 10px;color:{tc};font-weight:700;text-align:center">{pct:.0f}%</td>
          </tr>
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # PDF Download
    st.markdown('<p style="font-family:monospace;font-size:9.5px;letter-spacing:0.15em;color:#555;text-transform:uppercase;margin-bottom:8px">Generate PDF Report</p>', unsafe_allow_html=True)

    pdf_data = {
        "organization":   org,
        "proposal_title": title or "Untitled Proposal",
        "donor":          donor,
        "deadline":       str(deadline) if deadline else "",
        "evaluator":      evaluator,
        "date_evaluated": date.today().strftime("%Y-%m-%d"),
        "notes":          notes,
        "sections":       scores,
    }

    try:
        pdf_bytes = generate_pdf(pdf_data)
        filename  = f"{(title or 'proposal').replace(' ','_').lower()}_gonogo.pdf"
        st.download_button(
            label="⬇  Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"PDF generation error: {e}")
