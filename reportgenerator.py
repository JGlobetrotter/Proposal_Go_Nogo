generate report


#!/usr/bin/env python3
"""
Proposal Go/No-Go Diagnostic – PDF Report Generator
Usage:  python generate_report.py <input.json> [output.pdf]
"""

import json
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable

# ── Colour palette ────────────────────────────────────────────────────────────
C_GO        = colors.HexColor("#16a34a")   # green-600
C_GO_BG     = colors.HexColor("#dcfce7")   # green-100
C_CAUTION   = colors.HexColor("#d97706")   # amber-600
C_CAUTION_BG= colors.HexColor("#fef3c7")   # amber-100
C_NOGO      = colors.HexColor("#dc2626")   # red-600
C_NOGO_BG   = colors.HexColor("#fee2e2")   # red-100
C_PRIMARY   = colors.HexColor("#1e3a5f")   # dark navy
C_ACCENT    = colors.HexColor("#2563eb")   # blue-600
C_MUTED     = colors.HexColor("#6b7280")   # gray-500
C_BORDER    = colors.HexColor("#e5e7eb")   # gray-200
C_ROW_ALT   = colors.HexColor("#f9fafb")   # gray-50
C_HEADER_BG = colors.HexColor("#1e3a5f")
C_WHITE     = colors.white

SECTION_COLORS = {
    "Strategic Fit":           colors.HexColor("#7c3aed"),  # violet
    "Organizational Capacity": colors.HexColor("#0891b2"),  # cyan
    "Financial Viability":     colors.HexColor("#059669"),  # emerald
    "Risk Assessment":         colors.HexColor("#ea580c"),  # orange
}

SECTION_ICONS = {
    "Strategic Fit":           "🎯",
    "Organizational Capacity": "🏢",
    "Financial Viability":     "💰",
    "Risk Assessment":         "⚠️",
}

# ── Decision logic ─────────────────────────────────────────────────────────────
def compute_decision(sections: dict) -> tuple[str, int, int, float]:
    total = sum(s["score"] for s in sections.values())
    max_total = sum(s["max_score"] for s in sections.values())
    pct = total / max_total * 100

    if pct >= 70:
        verdict = "GO"
    elif pct >= 50:
        verdict = "PROCEED WITH CAUTION"
    else:
        verdict = "NO-GO"
    return verdict, total, max_total, pct


def section_label(score: int, max_score: int) -> str:
    pct = score / max_score * 100
    if pct >= 70: return "Strong"
    if pct >= 50: return "Moderate"
    return "Weak"


def decision_colors(verdict: str):
    if verdict == "GO":
        return C_GO, C_GO_BG
    elif verdict == "PROCEED WITH CAUTION":
        return C_CAUTION, C_CAUTION_BG
    else:
        return C_NOGO, C_NOGO_BG


def decision_emoji(verdict: str) -> str:
    return {"GO": "🟢", "PROCEED WITH CAUTION": "🟡", "NO-GO": "🔴"}.get(verdict, "")


# ── Custom flowables ───────────────────────────────────────────────────────────
class ScoreBar(Flowable):
    """A simple horizontal score bar."""
    def __init__(self, score, max_score, bar_color, width=3.5*inch, height=10):
        super().__init__()
        self.score = score
        self.max_score = max_score
        self.bar_color = bar_color
        self.width = width
        self.height = height

    def draw(self):
        pct = self.score / self.max_score
        # Background track
        self.canv.setFillColor(C_BORDER)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        # Filled portion
        if pct > 0:
            self.canv.setFillColor(self.bar_color)
            self.canv.roundRect(0, 0, self.width * pct, self.height, 4, fill=1, stroke=0)

    def wrap(self, *args):
        return self.width, self.height


# ── Report builder ─────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def make(name, **kw):
        s = ParagraphStyle(name, parent=base["Normal"], **kw)
        return s

    return {
        "cover_org":   make("cover_org",   fontSize=11, textColor=C_MUTED, alignment=TA_CENTER),
        "cover_title": make("cover_title", fontSize=22, textColor=C_PRIMARY,
                            fontName="Helvetica-Bold", leading=28, alignment=TA_CENTER),
        "cover_sub":   make("cover_sub",   fontSize=12, textColor=C_MUTED, alignment=TA_CENTER),
        "section_h":   make("section_h",   fontSize=13, textColor=C_PRIMARY,
                            fontName="Helvetica-Bold", spaceAfter=4),
        "label":       make("label",       fontSize=8.5, textColor=C_MUTED,
                            fontName="Helvetica-Bold", spaceBefore=2),
        "body":        make("body",        fontSize=10, textColor=colors.HexColor("#374151"), leading=15),
        "q_text":      make("q_text",      fontSize=9.5, textColor=colors.HexColor("#374151")),
        "q_score":     make("q_score",     fontSize=9.5, textColor=C_PRIMARY,
                            fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "verdict":     make("verdict",     fontSize=26, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "verdict_sub": make("verdict_sub", fontSize=11, textColor=C_MUTED, alignment=TA_CENTER),
        "footer":      make("footer",      fontSize=8, textColor=C_MUTED, alignment=TA_CENTER),
        "note_body":   make("note_body",   fontSize=9.5, textColor=colors.HexColor("#374151"),
                            leading=14, leftIndent=6),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    W, H = letter
    # Top bar
    canvas.setFillColor(C_HEADER_BG)
    canvas.rect(0, H - 36, W, 36, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(0.5*inch, H - 22, "PROPOSAL GO/NO-GO DIAGNOSTIC REPORT")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(W - 0.5*inch, H - 22, f"Page {doc.page}")
    # Bottom rule
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.5*inch, 0.45*inch, W - 0.5*inch, 0.45*inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawCentredString(W/2, 0.28*inch,
        "Confidential – For internal use only  |  Generated by Go/No-Go Diagnostic Tool")
    canvas.restoreState()


def build_cover(data: dict, verdict: str, total: int, max_total: int, pct: float,
                styles: dict) -> list:
    fg, bg = decision_colors(verdict)
    emoji = decision_emoji(verdict)
    story = []

    story.append(Spacer(1, 0.55*inch))
    story.append(Paragraph(data.get("organization", ""), styles["cover_org"]))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(data.get("proposal_title", "Untitled Proposal"), styles["cover_title"]))
    story.append(Spacer(1, 0.12*inch))
    story.append(Paragraph(
        f'Donor: {data.get("donor","—")}   |   Deadline: {data.get("deadline","—")}',
        styles["cover_sub"]
    ))
    story.append(Spacer(1, 0.45*inch))

    # Verdict banner
    banner_data = [[
        Paragraph(f'{emoji}  {verdict}', ParagraphStyle(
            "vb", parent=styles["verdict"], textColor=fg))
    ]]
    banner = Table(banner_data, colWidths=[5.5*inch])
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("TOPPADDING",    (0,0), (-1,-1), 18),
        ("BOTTOMPADDING", (0,0), (-1,-1), 18),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
        ("BOX",           (0,0), (-1,-1), 1.5, fg),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.35*inch))

    # Score summary row
    score_data = [
        [Paragraph("TOTAL SCORE", styles["label"]),
         Paragraph("PERCENTAGE", styles["label"]),
         Paragraph("EVALUATOR", styles["label"]),
         Paragraph("DATE", styles["label"])],
        [Paragraph(f"<b>{total} / {max_total}</b>",
                   ParagraphStyle("sv", fontSize=18, fontName="Helvetica-Bold",
                                  textColor=C_PRIMARY, alignment=TA_CENTER)),
         Paragraph(f"<b>{pct:.0f}%</b>",
                   ParagraphStyle("sp", fontSize=18, fontName="Helvetica-Bold",
                                  textColor=fg, alignment=TA_CENTER)),
         Paragraph(data.get("evaluator","—"), styles["body"]),
         Paragraph(data.get("date_evaluated","—"), styles["body"])],
    ]
    col_w = [1.3*inch, 1.3*inch, 2.0*inch, 1.3*inch]
    score_table = Table(score_data, colWidths=col_w)
    score_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), C_HEADER_BG),
        ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("GRID",         (0,0), (-1,-1), 0.5, C_BORDER),
        ("ROUNDEDCORNERS",(0,0),(-1,-1),[6,6,6,6]),
    ]))
    story.append(score_table)
    return story


def build_section_card(name: str, sec: dict, styles: dict, color) -> list:
    score, max_score = sec["score"], sec["max_score"]
    pct = score / max_score * 100
    lbl = section_label(score, max_score)
    icon = SECTION_ICONS.get(name, "")
    story = []

    # Section header row
    header_data = [[
        Paragraph(f'<b>{icon}  {name}</b>',
                  ParagraphStyle("sh", fontSize=12, fontName="Helvetica-Bold",
                                 textColor=C_WHITE)),
        Paragraph(f'<b>{score}/{max_score}  |  {pct:.0f}%  |  {lbl}</b>',
                  ParagraphStyle("ss", fontSize=10, fontName="Helvetica-Bold",
                                 textColor=C_WHITE, alignment=TA_RIGHT)),
    ]]
    header_t = Table(header_data, colWidths=[3.5*inch, 3.0*inch])
    header_t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), color),
        ("TOPPADDING",   (0,0), (-1,-1), 9),
        ("BOTTOMPADDING",(0,0), (-1,-1), 9),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(header_t)

    # Score bar
    bar = ScoreBar(score, max_score, color, width=6.5*inch, height=7)
    story.append(bar)
    story.append(Spacer(1, 6))

    # Question rows
    if "questions" in sec:
        q_rows = [["Question", "Score", "Max"]]
        for q in sec["questions"]:
            q_rows.append([
                Paragraph(q["question"], styles["q_text"]),
                Paragraph(str(q["score"]), styles["q_score"]),
                Paragraph(str(q["max"]), styles["q_score"]),
            ])
        q_table = Table(q_rows, colWidths=[4.9*inch, 0.8*inch, 0.8*inch])
        q_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), C_HEADER_BG),
            ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 8.5),
            ("ALIGN",        (1,0), (-1,-1), "CENTER"),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_ROW_ALT]),
            ("GRID",         (0,0), (-1,-1), 0.4, C_BORDER),
            ("TOPPADDING",   (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 6),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(q_table)

    story.append(Spacer(1, 0.22*inch))
    return story


def build_summary_table(sections: dict, styles: dict) -> list:
    story = [Paragraph("Section Score Summary", styles["section_h"]),
             Spacer(1, 6)]

    rows = [["Section", "Score", "Max", "%", "Rating"]]
    total_s, total_m = 0, 0
    for name, sec in sections.items():
        s, m = sec["score"], sec["max_score"]
        total_s += s; total_m += m
        pct = s / m * 100
        lbl = section_label(s, m)
        rows.append([
            Paragraph(f'{SECTION_ICONS.get(name,"")} {name}', styles["q_text"]),
            Paragraph(str(s), styles["q_score"]),
            Paragraph(str(m), styles["q_score"]),
            Paragraph(f"{pct:.0f}%", styles["q_score"]),
            Paragraph(lbl, styles["q_score"]),
        ])
    # Totals row
    rows.append([
        Paragraph("<b>TOTAL</b>", ParagraphStyle("tb", fontSize=10,
                  fontName="Helvetica-Bold", textColor=C_PRIMARY)),
        Paragraph(f"<b>{total_s}</b>", ParagraphStyle("ts", fontSize=10,
                  fontName="Helvetica-Bold", textColor=C_PRIMARY, alignment=TA_RIGHT)),
        Paragraph(f"<b>{total_m}</b>", ParagraphStyle("tm", fontSize=10,
                  fontName="Helvetica-Bold", textColor=C_PRIMARY, alignment=TA_RIGHT)),
        Paragraph(f"<b>{total_s/total_m*100:.0f}%</b>", ParagraphStyle(
                  "tp", fontSize=10, fontName="Helvetica-Bold",
                  textColor=C_ACCENT, alignment=TA_RIGHT)),
        Paragraph("", styles["q_score"]),
    ])

    t = Table(rows, colWidths=[2.8*inch, 0.7*inch, 0.7*inch, 0.8*inch, 1.5*inch])
    n = len(rows)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),   C_HEADER_BG),
        ("TEXTCOLOR",     (0,0), (-1,0),   C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),   8.5),
        ("ALIGN",         (1,0), (-1,-1),  "CENTER"),
        ("VALIGN",        (0,0), (-1,-1),  "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1), (-1,n-2), [C_WHITE, C_ROW_ALT]),
        ("BACKGROUND",    (0,n-1),(-1,n-1), colors.HexColor("#e0e7ff")),
        ("GRID",          (0,0), (-1,-1),  0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1),  7),
        ("BOTTOMPADDING", (0,0), (-1,-1),  7),
        ("LEFTPADDING",   (0,0), (-1,-1),  8),
        ("RIGHTPADDING",  (0,0), (-1,-1),  8),
    ]))
    story.append(t)
    return story


def generate_narrative(verdict: str, pct: float, sections: dict,
                        proposal_title: str, notes: str) -> tuple[str, str]:
    """Rule-based narrative generator (no API required)."""

    section_names = {
        "strategic_fit": "Strategic Fit",
        "organizational_capacity": "Organizational Capacity",
        "financial_viability": "Financial Viability",
        "risk_assessment": "Risk Assessment",
    }

    strengths = []
    weaknesses = []
    for key, sec in sections.items():
        s, m = sec["score"], sec["max_score"]
        name = section_names.get(key, key)
        lbl = section_label(s, m)
        if lbl == "Strong":
            strengths.append(name)
        elif lbl == "Weak":
            weaknesses.append(name)

    def fmt_list(lst):
        if not lst: return ""
        if len(lst) == 1: return lst[0]
        return ", ".join(lst[:-1]) + " and " + lst[-1]

    if verdict == "GO":
        summary = (
            f'The proposal "<b>{proposal_title}</b>" has achieved a composite score of '
            f'<b>{pct:.0f}%</b>, indicating a strong overall readiness to pursue this '
            f'opportunity. '
        )
        if strengths:
            summary += (f'The organization demonstrates clear strength in {fmt_list(strengths)}, '
                        f'which provides a solid foundation for successful delivery. ')
        if weaknesses:
            summary += (f'While {fmt_list(weaknesses)} scored below the strong threshold, '
                        f'these areas should be monitored during implementation. ')
        summary += ('Overall, the opportunity aligns well with organisational priorities '
                    'and the risk-adjusted case for proceeding is positive.')

        next_steps = (
            '<b>Recommended Next Steps:</b><br/>'
            '1. Initiate internal proposal kick-off meeting within 5 working days.<br/>'
            '2. Assign a dedicated proposal coordinator and establish a writing schedule.<br/>'
            '3. Begin partnership outreach and letters of support collection immediately.<br/>'
            '4. Develop a budget framework and confirm cost-share or matching requirements.<br/>'
            '5. Schedule a pre-submission review with the Programme Director.'
        )

    elif verdict == "PROCEED WITH CAUTION":
        summary = (
            f'The proposal "<b>{proposal_title}</b>" has achieved a composite score of '
            f'<b>{pct:.0f}%</b>, indicating moderate readiness. The opportunity warrants '
            f'serious consideration, but several issues require resolution before committing '
            f'full resources. '
        )
        if strengths:
            summary += f'Key strengths include {fmt_list(strengths)}. '
        if weaknesses:
            summary += (f'However, {fmt_list(weaknesses)} present notable gaps that could '
                        f'undermine proposal quality or delivery success if left unaddressed. ')
        summary += ('A conditional go-ahead is recommended, contingent on a clear mitigation '
                    'plan for identified weaknesses.')

        next_steps = (
            '<b>Recommended Next Steps:</b><br/>'
            '1. Convene a rapid risk-review meeting to assess gaps in weak-scoring areas.<br/>'
            '2. Identify whether partnerships can offset internal capacity shortfalls.<br/>'
            '3. Obtain senior leadership sign-off before committing proposal-writing resources.<br/>'
            '4. Develop a risk register and mitigation plan as part of the proposal narrative.<br/>'
            '5. Re-evaluate the decision if additional red flags emerge during preparation.'
        )

    else:  # NO-GO
        summary = (
            f'The proposal "<b>{proposal_title}</b>" has achieved a composite score of '
            f'<b>{pct:.0f}%</b>, falling below the minimum threshold required to recommend '
            f'pursuit. Significant deficiencies across multiple dimensions suggest that '
            f'proceeding would carry unacceptably high risk of failure or organisational harm. '
        )
        if weaknesses:
            summary += (f'Critical weaknesses were identified in {fmt_list(weaknesses)}, '
                        f'which are unlikely to be resolved within the available timeframe. ')
        summary += ('Declining this opportunity allows the team to focus capacity on '
                    'higher-probability proposals and avoids potential reputational or '
                    'financial exposure.')

        next_steps = (
            '<b>Recommended Next Steps:</b><br/>'
            '1. Communicate the No-Go decision promptly to all internal stakeholders.<br/>'
            '2. Document lessons learned for future opportunity assessments.<br/>'
            '3. Consider whether a partnership or sub-grant role might still be feasible.<br/>'
            '4. Explore alternative funding opportunities that better match current capacity.<br/>'
            '5. Use this diagnostic to build a capacity-strengthening plan for future bids.'
        )

    return summary, next_steps


def generate_report_from_data(data: dict, output_path: str):
    """Core report builder – accepts a data dict directly."""
    sections_raw = data.get("sections", {})
    section_display = {
        "strategic_fit":           "Strategic Fit",
        "organizational_capacity": "Organizational Capacity",
        "financial_viability":     "Financial Viability",
        "risk_assessment":         "Risk Assessment",
    }

    verdict, total, max_total, pct = compute_decision(sections_raw)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.7*inch,   bottomMargin=0.7*inch,
    )

    styles = build_styles()
    story  = []

    story += build_cover(data, verdict, total, max_total, pct, styles)
    story.append(Spacer(1, 0.35*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("✦  Diagnostic Analysis", styles["section_h"]))
    story.append(Spacer(1, 6))

    summary_text, next_steps_text = generate_narrative(
        verdict, pct, sections_raw,
        data.get("proposal_title", "this proposal"),
        data.get("notes", "")
    )

    analysis_rows = [
        [Paragraph("Executive Summary", ParagraphStyle(
            "alh", fontSize=9, fontName="Helvetica-Bold", textColor=C_ACCENT))],
        [Paragraph(summary_text, styles["body"])],
        [Spacer(1, 6)],
        [Paragraph("Strategic Next Steps", ParagraphStyle(
            "alh2", fontSize=9, fontName="Helvetica-Bold", textColor=C_ACCENT))],
        [Paragraph(next_steps_text, styles["body"])],
    ]
    if data.get("notes"):
        analysis_rows += [
            [Spacer(1, 4)],
            [Paragraph("Evaluator Notes", ParagraphStyle(
                "alh3", fontSize=9, fontName="Helvetica-Bold", textColor=C_MUTED))],
            [Paragraph(data["notes"], styles["note_body"])],
        ]

    analysis_table = Table(analysis_rows, colWidths=[6.5*inch])
    analysis_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f5f3ff")),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("BOX",           (0,0), (-1,-1), 1, colors.HexColor("#7c3aed")),
        ("LINEAFTER",     (0,0), (0,-1),  3, colors.HexColor("#7c3aed")),
    ]))
    story.append(analysis_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3*inch))

    story += build_summary_table(sections_raw, styles)
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Detailed Section Scores", styles["section_h"]))
    story.append(Spacer(1, 8))

    for key, sec in sections_raw.items():
        display_name = section_display.get(key, key.replace("_", " ").title())
        color = SECTION_COLORS.get(display_name, C_ACCENT)
        card  = build_section_card(display_name, sec, styles, color)
        story.append(KeepTogether(card))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"✅  Report saved to: {output_path}")


# ── CLI entry point ────────────────────────────────────────────────────────────
import argparse as _argparse

def main():
    parser = _argparse.ArgumentParser(
        description="Generate a Proposal Go/No-Go Diagnostic PDF report.",
        formatter_class=_argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimal – scores only, all other fields optional:
  python generate_report.py --sf 16 --oc 13 --fv 14 --ra 10

  # Full report with all metadata:
  python generate_report.py \\
      --org "Hope Bridge Foundation" \\
      --title "Clean Water Access – Rural Kenya" \\
      --donor "USAID Water & Sanitation Initiative" \\
      --deadline 2025-03-15 \\
      --evaluator "Sarah Kimani" \\
      --sf 16 --oc 13 --fv 14 --ra 10 \\
      --notes "Elevated political risk; recommend phased rollout." \\
      --output my_report.pdf

  # With per-question scores (comma-separated, must sum to section score):
  python generate_report.py \\
      --sf 16 --sf-q "Mission alignment:4,5" "Existing expertise:4,5" "Donor relations:4,5" "Strategic goals:4,5" \\
      --oc 13 --fv 14 --ra 10
        """
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    meta = parser.add_argument_group("Proposal metadata (all optional)")
    meta.add_argument("--org",       metavar="TEXT",  default="",
                      help="Organisation name")
    meta.add_argument("--title",     metavar="TEXT",  default="Untitled Proposal",
                      help="Proposal title")
    meta.add_argument("--donor",     metavar="TEXT",  default="",
                      help="Donor / funder name")
    meta.add_argument("--deadline",  metavar="DATE",  default="",
                      help="Submission deadline (any text, e.g. 2025-03-15)")
    meta.add_argument("--evaluator", metavar="TEXT",  default="",
                      help="Evaluator name")
    meta.add_argument("--date",      metavar="DATE",
                      default=datetime.today().strftime("%Y-%m-%d"),
                      help="Evaluation date (default: today)")
    meta.add_argument("--notes",     metavar="TEXT",  default="",
                      help="Free-text evaluator notes appended to the report")
    meta.add_argument("--output",    metavar="FILE",  default="go_nogo_report.pdf",
                      help="Output PDF path (default: go_nogo_report.pdf)")

    # ── Section scores ────────────────────────────────────────────────────────
    scores = parser.add_argument_group(
        "Section scores (required)",
        "Pass the total score for each section out of 20."
    )
    scores.add_argument("--sf",  type=int, required=True, metavar="0-20",
                        help="Strategic Fit score (0–20)")
    scores.add_argument("--oc",  type=int, required=True, metavar="0-20",
                        help="Organizational Capacity score (0–20)")
    scores.add_argument("--fv",  type=int, required=True, metavar="0-20",
                        help="Financial Viability score (0–20)")
    scores.add_argument("--ra",  type=int, required=True, metavar="0-20",
                        help="Risk Assessment score (0–20)")

    # ── Per-question detail (optional) ────────────────────────────────────────
    detail = parser.add_argument_group(
        "Per-question detail (optional)",
        'Each question uses format  "Question text:score,max"  e.g. "Mission alignment:4,5"'
    )
    detail.add_argument("--sf-q", nargs="+", metavar="Q", default=None,
                        help="Strategic Fit questions")
    detail.add_argument("--oc-q", nargs="+", metavar="Q", default=None,
                        help="Organizational Capacity questions")
    detail.add_argument("--fv-q", nargs="+", metavar="Q", default=None,
                        help="Financial Viability questions")
    detail.add_argument("--ra-q", nargs="+", metavar="Q", default=None,
                        help="Risk Assessment questions")

    args = parser.parse_args()

    # ── Validate scores ───────────────────────────────────────────────────────
    for flag, val in [("--sf", args.sf), ("--oc", args.oc),
                      ("--fv", args.fv), ("--ra", args.ra)]:
        if not 0 <= val <= 20:
            parser.error(f"{flag} must be between 0 and 20 (got {val})")

    # ── Parse per-question strings ────────────────────────────────────────────
    def parse_questions(raw_list):
        """Parse ["Question text:score,max", ...] into dicts."""
        if not raw_list:
            return None
        questions = []
        for item in raw_list:
            try:
                label, nums = item.rsplit(":", 1)
                s, m = nums.split(",")
                questions.append({"question": label.strip(),
                                   "score": int(s), "max": int(m)})
            except ValueError:
                parser.error(
                    f'Could not parse question "{item}". '
                    'Expected format: "Question text:score,max"  e.g. "Mission alignment:4,5"'
                )
        return questions

    def make_section(score, max_score, raw_q):
        sec = {"score": score, "max_score": max_score}
        qs = parse_questions(raw_q)
        if qs:
            sec["questions"] = qs
        else:
            # Generate generic placeholder questions so the table still renders
            per_q = max_score // 4
            remaining = score
            generic = []
            labels = ["Criterion A", "Criterion B", "Criterion C", "Criterion D"]
            for i, lbl in enumerate(labels):
                q_score = min(remaining, per_q)
                remaining -= q_score
                generic.append({"question": lbl, "score": q_score, "max": per_q})
            sec["questions"] = generic
        return sec

    # ── Assemble data dict (mirrors JSON schema) ──────────────────────────────
    data = {
        "organization":   args.org,
        "proposal_title": args.title,
        "donor":          args.donor,
        "deadline":       args.deadline,
        "evaluator":      args.evaluator,
        "date_evaluated": args.date,
        "notes":          args.notes,
        "sections": {
            "strategic_fit":           make_section(args.sf, 20, args.sf_q),
            "organizational_capacity": make_section(args.oc, 20, args.oc_q),
            "financial_viability":     make_section(args.fv, 20, args.fv_q),
            "risk_assessment":         make_section(args.ra, 20, args.ra_q),
        }
    }

    # ── Generate ──────────────────────────────────────────────────────────────
    verdict, total, max_total, pct = compute_decision(data["sections"])
    print(f"\n📋  Proposal : {data['proposal_title']}")
    print(f"📊  Score    : {total}/{max_total}  ({pct:.0f}%)")
    print(f"🔖  Decision : {verdict}\n")

    generate_report_from_data(data, args.output)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
