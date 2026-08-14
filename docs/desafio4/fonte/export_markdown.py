# -*- coding: utf-8 -*-
"""Exporta a fonte do relatório (report_content.py) como Markdown legível/editável."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_content import COVER, BLOCKS

OUT_PATH = os.environ["REPORT_OUT_MD"]

lines = []
lines.append(f"# {COVER['program']} — {COVER['challenge']}")
lines.append("")
lines.append(f"## {COVER['title']}")
lines.append("")
lines.append(f"**Projeto:** {COVER['project_name']}  ")
lines.append(f"**Grupo:** {COVER['group_name']}  ")
lines.append(f"**Integrantes:** {COVER['members']}  ")
lines.append(f"**Data:** {COVER['date']}")
lines.append("")
lines.append("---")
lines.append("")

for block in BLOCKS:
    kind = block[0]
    if kind == "h1":
        lines.append(f"## {block[1]}")
        lines.append("")
    elif kind == "h2":
        lines.append(f"### {block[1]}")
        lines.append("")
    elif kind == "h3":
        lines.append(f"#### {block[1]}")
        lines.append("")
    elif kind == "p":
        lines.append(block[1])
        lines.append("")
    elif kind in ("bullets", "numbered"):
        for i, item in enumerate(block[1], start=1):
            prefix = f"{i}." if kind == "numbered" else "-"
            lines.append(f"{prefix} {item}")
        lines.append("")
    elif kind == "table":
        spec = block[1]
        header = spec["header"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for row in spec["rows"]:
            cells = [str(v).replace("\n", " ").replace("|", "\\|") for v in row]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    elif kind == "image":
        lines.append(f"![{block[2]}](assets/{block[1]})")
        lines.append("")
        lines.append(f"*{block[2]}*")
        lines.append("")
    elif kind == "note":
        lines.append(f"> **Nota:** {block[1]}")
        lines.append("")
    elif kind == "pagebreak":
        lines.append("---")
        lines.append("")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("saved", OUT_PATH)
