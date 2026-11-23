"""Render docs/INTRODUCTION.md into a formatted Word document."""

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "INTRODUCTION.md"
OUT = ROOT / "docs" / "INTRODUCTION.docx"

doc = Document()

# Page + base style
for section in doc.sections:
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

ACCENT = RGBColor(0x1F, 0x3B, 0x57)


def clean(text):
    """Strip markdown emphasis and inline code, return (text, bold_spans)."""
    text = text.replace("**", "").replace("`", "")
    return text.strip()


def add_body(text, style=None):
    text = clean(text)
    if not text:
        return
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.size = Pt(11)
    return p


def add_bullet(text, numbered=False):
    text = clean(text)
    # bold the leading phrase before an em dash
    style = "List Number" if numbered else "List Bullet"
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(3)
    if " — " in text and text.index(" — ") < 90:
        head, tail = text.split(" — ", 1)
        r = p.add_run(head)
        r.bold = True
        r.font.size = Pt(11)
        p.add_run(" — " + tail).font.size = Pt(11)
    else:
        p.add_run(text).font.size = Pt(11)
    return p


lines = SRC.read_text(encoding="utf-8").splitlines()
i = 0
in_header = True

while i < len(lines):
    line = lines[i].rstrip()
    stripped = line.strip()

    if stripped == "---":
        i += 1
        continue

    if stripped.startswith("# "):
        title = clean(stripped[2:])
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(24)
        r.font.color.rgb = ACCENT
        i += 1
        continue

    if stripped.startswith("## "):
        in_header = False
        heading = clean(stripped[3:])
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(heading)
        r.bold = True
        r.font.size = Pt(14)
        r.font.color.rgb = ACCENT
        # thin rule under the heading
        pPr = p._p.get_or_add_pPr()
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "2")
        bottom.set(qn("w:color"), "C7D2DC")
        borders.append(bottom)
        pPr.append(borders)
        i += 1
        continue

    if stripped.startswith("- "):
        # gather this bullet's wrapped continuation lines
        parts = [stripped[2:]]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            parts.append(lines[i].strip())
            i += 1
        add_bullet(" ".join(parts))
        continue

    m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
    if m:
        parts = [m.group(2)]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            parts.append(lines[i].strip())
            i += 1
        add_bullet(" ".join(parts), numbered=True)
        continue

    if in_header:
        # Title block: every line stands alone, centred.
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(clean(stripped))
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(0x44, 0x4F, 0x5A)
        i += 1
        continue

    # Plain text: join wrapped source lines into one flowing paragraph.
    parts = [stripped]
    i += 1
    while i < len(lines):
        nxt = lines[i].strip()
        if (
            not nxt
            or nxt.startswith(("#", "- ", "---"))
            or re.match(r"^\d+\.\s", nxt)
        ):
            break
        parts.append(nxt)
        i += 1
    add_body(" ".join(parts))

doc.save(OUT)
print("saved", OUT)
print("paragraphs:", len(doc.paragraphs))
