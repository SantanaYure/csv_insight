# -*- coding: utf-8 -*-
"""PDF de conferência visual da versão acessível do relatório (não é a entrega final)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_content_v2 import COVER, BLOCKS

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, HRFlowable
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

NAVY = colors.HexColor("#17324A")
BLUE = colors.HexColor("#2E6C9E")
GRAY = colors.HexColor("#5B6770")
LIGHT_BG = colors.HexColor("#EAF2F8")
QA_BG = colors.HexColor("#F2F6F9")
DARK_TEXT = colors.HexColor("#222222")

ASSETS_DIR = os.environ["REPORT_ASSETS_DIR"]
OUT_PATH = os.environ["REPORT_OUT_PDF"]

PAGE_W, PAGE_H = A4
MARGIN = 2.4 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

body_style = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.6, leading=15.5,
                             textColor=DARK_TEXT, alignment=TA_JUSTIFY, spaceAfter=9)
h1_style = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15.5, leading=19,
                           textColor=NAVY, spaceBefore=18, spaceAfter=10)
bullet_style = ParagraphStyle("Bullet", parent=body_style, spaceAfter=6, leading=14.8,
                               leftIndent=14, firstLineIndent=-14)
caption_style = ParagraphStyle("Caption", fontName="Helvetica-Oblique", fontSize=9,
                                textColor=GRAY, alignment=TA_CENTER, spaceAfter=14, spaceBefore=6)


class FlowBox(Flowable):
    def __init__(self, steps, width):
        super().__init__()
        self.width = width
        text = "&nbsp;&nbsp;&rarr;&nbsp;&nbsp;".join(steps)
        style = ParagraphStyle("Flow", fontName="Helvetica-Bold", fontSize=10, leading=15,
                                textColor=NAVY, alignment=TA_CENTER)
        self.para = Paragraph(text, style)

    def wrap(self, availWidth, availHeight):
        w, h = self.para.wrap(self.width - 24, availHeight)
        self.height = h + 18
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, self.width, self.height, 6, stroke=0, fill=1)
        self.para.drawOn(c, 12, 9)


class QABox(Flowable):
    def __init__(self, question, width):
        super().__init__()
        self.width = width
        qstyle = ParagraphStyle("Q", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=NAVY)
        astyle = ParagraphStyle("A", fontName="Helvetica-Oblique", fontSize=10.4, leading=14, textColor=GRAY)
        lstyle = ParagraphStyle("L", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=BLUE)
        self.p_label_q = Paragraph("PERGUNTA", lstyle)
        self.p_q = Paragraph(question, qstyle)
        self.p_label_a = Paragraph("RESPOSTA", lstyle)
        self.p_a = Paragraph("(resposta a inserir)", astyle)

    def wrap(self, availWidth, availHeight):
        pad = 16
        w = self.width - 2 * pad
        h1 = self.p_label_q.wrap(w, availHeight)[1]
        h2 = self.p_q.wrap(w, availHeight)[1]
        h3 = self.p_label_a.wrap(w, availHeight)[1]
        h4 = self.p_a.wrap(w, availHeight)[1]
        self.height = h1 + h2 + h3 + h4 + 3 * 4 + 2 * pad
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(QA_BG)
        c.roundRect(0, 0, self.width, self.height, 6, stroke=0, fill=1)
        c.setFillColor(BLUE)
        c.rect(0, 0, 3, self.height, stroke=0, fill=1)
        pad = 16
        y = self.height - pad
        for para in (self.p_label_q, self.p_q, self.p_label_a, self.p_a):
            w, h = para.wrap(self.width - 2 * pad, self.height)
            y -= h
            para.drawOn(c, pad, y)
            y -= 4


def bullets_flowable(items):
    return [Paragraph(f"<b>&bull;</b>&nbsp;&nbsp;{item}", bullet_style) for item in items]


def build_story():
    story = []
    for block in BLOCKS:
        kind = block[0]
        if kind == "h1":
            story.append(HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceAfter=2, spaceBefore=12))
            story.append(Paragraph(block[1], h1_style))
        elif kind == "p":
            story.append(Paragraph(block[1], body_style))
        elif kind == "bullets":
            story.extend(bullets_flowable(block[1]))
            story.append(Spacer(1, 6))
        elif kind == "image":
            img_path = os.path.join(ASSETS_DIR, block[1])
            from PIL import Image as PILImage
            iw, ih = PILImage.open(img_path).size
            display_w = CONTENT_W * 0.95
            display_h = display_w * ih / iw
            story.append(Spacer(1, 4))
            story.append(Image(img_path, width=display_w, height=display_h, hAlign="CENTER"))
            story.append(Paragraph(block[2], caption_style))
        elif kind == "flow":
            story.append(FlowBox(block[1], CONTENT_W))
            story.append(Spacer(1, 12))
        elif kind == "qa":
            story.append(QABox(block[1], CONTENT_W))
            story.append(Spacer(1, 10))
        elif kind == "pagebreak":
            story.append(PageBreak())
    return story


def draw_cover(c):
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
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(PAGE_W / 2, y, f"Grupo: {COVER['group_name']}")
    y -= 0.7 * cm
    c.drawCentredString(PAGE_W / 2, y, f"Integrantes: {COVER['members']}")

    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_W / 2, 3.0 * cm, COVER["date"])
    c.restoreState()


def header_footer(c: canvas.Canvas, doc):
    if doc.page == 1:
        draw_cover(c)
        return
    c.saveState()
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawCentredString(PAGE_W / 2, 1.3 * cm, "CSV Insight  ·  InsurMinds  ·  Desafio 4")
    c.restoreState()


def main():
    doc = SimpleDocTemplate(OUT_PATH, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                             topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                             title="InsurMinds - Desafio 4 - CSV Insight")
    story = [PageBreak()] + build_story()
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()
