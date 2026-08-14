# -*- coding: utf-8 -*-
"""Gera InsurMinds_Desafio4_Relatorio_Tecnico.pdf a partir de report_content.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_content import COVER, BLOCKS

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

NAVY = colors.HexColor("#17324A")
BLUE = colors.HexColor("#2E6C9E")
GRAY = colors.HexColor("#5B6770")
LIGHT_BG = colors.HexColor("#EAF2F8")
HEADER_BG = colors.HexColor("#17324A")
ROW_ALT = colors.HexColor("#F5F8FA")
DARK_TEXT = colors.HexColor("#222222")
PENDING_RED = colors.HexColor("#B03A2E")

ASSETS_DIR = os.environ["REPORT_ASSETS_DIR"]
OUT_PATH = os.environ["REPORT_OUT_PDF"]

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

styles = getSampleStyleSheet()

body_style = ParagraphStyle(
    "Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10.2,
    leading=14.2, textColor=DARK_TEXT, alignment=TA_JUSTIFY, spaceAfter=7,
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15.5,
    leading=19, textColor=NAVY, spaceBefore=16, spaceAfter=9,
)
h2_style = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.3,
    leading=15, textColor=NAVY, spaceBefore=11, spaceAfter=6,
)
h3_style = ParagraphStyle(
    "H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.8,
    leading=13.5, textColor=BLUE, spaceBefore=8, spaceAfter=4,
)
bullet_style = ParagraphStyle(
    "Bullet", parent=body_style, spaceAfter=4, leading=13.6,
    leftIndent=14, firstLineIndent=-14,
)
note_style = ParagraphStyle(
    "Note", parent=body_style, fontName="Helvetica-Oblique", fontSize=9.4,
    leading=13, textColor=colors.HexColor("#334455"), alignment=TA_LEFT,
    backColor=LIGHT_BG, borderColor=BLUE, borderWidth=0, leftIndent=10,
    spaceBefore=4, spaceAfter=9,
)
cell_style = ParagraphStyle(
    "Cell", parent=body_style, fontSize=8.4, leading=11, alignment=TA_LEFT, spaceAfter=0,
)
cell_header_style = ParagraphStyle(
    "CellHeader", parent=cell_style, fontName="Helvetica-Bold", fontSize=8.8,
    textColor=colors.white, alignment=TA_LEFT,
)
caption_style = ParagraphStyle(
    "Caption", parent=body_style, fontName="Helvetica-Oblique", fontSize=8.6,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=10, spaceBefore=4,
)


class NoteBox(Flowable):
    """Left-accent-bordered, shaded note block (a Table wrapper would clip text)."""

    def __init__(self, text, width):
        super().__init__()
        self.width = width
        self.para = Paragraph(text, note_style)

    def wrap(self, availWidth, availHeight):
        w, h = self.para.wrap(self.width - 14, availHeight)
        self.height = h + 10
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT_BG)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(BLUE)
        c.rect(0, 0, 3, self.height, stroke=0, fill=1)
        self.para.drawOn(c, 12, 5)


def note_flowable(text):
    return NoteBox(text, CONTENT_W)


def make_table(spec):
    header = spec["header"]
    rows = spec["rows"]
    fracs = spec.get("col_widths_frac") or [1.0 / len(header)] * len(header)
    col_widths = [CONTENT_W * f for f in fracs]

    data = [[Paragraph(h, cell_header_style) for h in header]]
    for row in rows:
        data.append([Paragraph(str(v), cell_style) for v in row])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D2D9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def bullets_flowable(items, numbered=False):
    flowables = []
    for i, item in enumerate(items, start=1):
        prefix = f"{i}." if numbered else "•"
        flowables.append(Paragraph(f"<b>{prefix}</b>&nbsp;&nbsp;{item}", bullet_style))
    return flowables


def build_story():
    story = []
    for block in BLOCKS:
        kind = block[0]
        if kind == "h1":
            story.append(HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceAfter=2, spaceBefore=10))
            story.append(Paragraph(block[1], h1_style))
        elif kind == "h2":
            story.append(Paragraph(block[1], h2_style))
        elif kind == "h3":
            story.append(Paragraph(block[1], h3_style))
        elif kind == "p":
            story.append(Paragraph(block[1], body_style))
        elif kind == "bullets":
            story.extend(bullets_flowable(block[1], numbered=False))
            story.append(Spacer(1, 6))
        elif kind == "numbered":
            story.extend(bullets_flowable(block[1], numbered=True))
            story.append(Spacer(1, 6))
        elif kind == "table":
            story.append(make_table(block[1]))
            story.append(Spacer(1, 10))
        elif kind == "image":
            img_path = os.path.join(ASSETS_DIR, block[1])
            from PIL import Image as PILImage
            iw, ih = PILImage.open(img_path).size
            display_w = CONTENT_W * 0.92
            display_h = display_w * ih / iw
            max_h = 21 * cm
            if display_h > max_h:
                display_h = max_h
                display_w = display_h * iw / ih
            story.append(Spacer(1, 4))
            story.append(Image(img_path, width=display_w, height=display_h, hAlign="CENTER"))
            story.append(Paragraph(block[2], caption_style))
        elif kind == "note":
            story.append(note_flowable(block[1]))
        elif kind == "pagebreak":
            story.append(PageBreak())
    return story


def draw_cover(c, doc_width, doc_height):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 3.2 * cm, PAGE_W, 3.2 * cm, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 3.55 * cm, PAGE_W, 0.35 * cm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.1 * cm, COVER["program"])
    c.setFont("Helvetica", 11)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.75 * cm, COVER["subtitle"])

    y = PAGE_H - 7.5 * cm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W / 2, y, COVER["challenge"])

    y -= 1.0 * cm
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica", 14)
    c.drawCentredString(PAGE_W / 2, y, COVER["title"])

    y -= 2.0 * cm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(PAGE_W / 2, y, f"Projeto: {COVER['project_name']}")

    y -= 0.9 * cm
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(PENDING_RED)
    c.drawCentredString(PAGE_W / 2, y, f"Grupo: {COVER['group_name']}")
    y -= 0.7 * cm
    c.drawCentredString(PAGE_W / 2, y, f"Integrantes: {COVER['members']}")

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_W / 2, 3.4 * cm, f"Relatório técnico gerado em {COVER['date']}")
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawCentredString(
        PAGE_W / 2, 2.85 * cm,
        "Documento elaborado com base exclusiva no código do repositório do projeto.",
    )
    c.restoreState()


def header_footer(c: canvas.Canvas, doc):
    if doc.page == 1:
        draw_cover(c, doc.width, doc.height)
        return
    c.saveState()
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawCentredString(PAGE_W / 2, 1.3 * cm, f"CSV Insight — InsurMinds — Desafio 4  |  página {doc.page}")
    c.restoreState()


def main():
    doc = SimpleDocTemplate(
        OUT_PATH, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=2.0 * cm, bottomMargin=2.0 * cm,
        title="InsurMinds - Desafio 4 - Relatorio Tecnico - CSV Insight",
    )
    story = [PageBreak()] + build_story()
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()
