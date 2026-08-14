# -*- coding: utf-8 -*-
"""Diagrama simplificado (sem nomes de arquivo/classe) para a versão de leitura geral."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#17324A"
BLUE = "#2E6C9E"
LIGHT_BLUE = "#EAF2F8"
GRAY = "#5B6770"
WHITE = "#FFFFFF"

fig, ax = plt.subplots(figsize=(9.2, 6.4))
ax.set_xlim(0, 11.5)
ax.set_ylim(0, 5.3)
ax.axis("off")

def box(x, y, w, h, text, fc=WHITE, ec=NAVY, tc=NAVY, fs=12, lw=1.8):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.14",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fs, color=tc, weight="bold", zorder=3, linespacing=1.3)
    return (x, y, w, h)

def arrow(b1, b2, bidir=False, color=NAVY, lw=2.0, label=None, label_dy=0.22):
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    start = (x1 + w1, y1 + h1 / 2)
    end = (x2, y2 + h2 / 2)
    style = "<|-|>" if bidir else "-|>"
    a = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=16, linewidth=lw, color=color, zorder=1)
    ax.add_patch(a)
    if label:
        ax.text((start[0] + end[0]) / 2, start[1] + label_dy, label, fontsize=8.6,
                 color=GRAY, ha="center", va="bottom", style="italic")

ax.text(5.75, 5.05, "Como as partes da solução se conectam", ha="center", va="center",
        fontsize=14.5, color=NAVY, weight="bold")

H = 1.15
usuario = box(0.3, 3.15, 1.7, H, "Usuário", fc=LIGHT_BLUE, fs=11.5)
interface = box(2.55, 3.15, 1.9, H, "Interface", fs=11)
backend = box(4.95, 3.15, 1.9, H, "Backend", fs=11)
agente = box(7.35, 3.15, 2.0, H, "Agente\nde IA", fs=11)
ferramentas = box(7.35, 1.1, 2.0, H, "Ferramentas\nde consulta", fs=10.3)
dados = box(4.95, 1.1, 1.9, H, "Dados\nprocessados", fs=10.3)

arrow(usuario, interface)
arrow(interface, backend)
arrow(backend, agente)
ax.annotate("", xy=(ferramentas[0] + ferramentas[2] / 2, ferramentas[1] + ferramentas[3]),
            xytext=(agente[0] + agente[2] / 2, agente[1]),
            arrowprops=dict(arrowstyle="<|-|>", color=NAVY, lw=2.0))
ax.annotate("", xy=(dados[0] + dados[2], dados[1] + dados[3] / 2),
            xytext=(ferramentas[0], ferramentas[1] + ferramentas[3] / 2),
            arrowprops=dict(arrowstyle="<|-|>", color=NAVY, lw=2.0))
ax.annotate("", xy=(backend[0] + backend[2] / 2, backend[1]),
            xytext=(dados[0] + dados[2] / 2, dados[1] + dados[3]),
            arrowprops=dict(arrowstyle="<|-|>", color=BLUE, lw=1.6, linestyle=(0, (4, 3))))

ax.text(8.75, 2.68, "consulta e\nrecebe resultado", fontsize=8, color=GRAY, ha="left", style="italic")
ax.text(3.75, 2.68, "guarda e lê\nos dados", fontsize=8, color=GRAY, ha="center", style="italic")

ax.text(5.75, 0.35,
        "O usuário conversa pela interface; o backend organiza os dados e aciona o agente;\n"
        "o agente usa as ferramentas de consulta para buscar a resposta nos dados processados.",
        ha="center", va="center", fontsize=9, color=GRAY, linespacing=1.5)

plt.tight_layout()
out = os.path.join(os.environ["REPORT_ASSETS_DIR"], "arquitetura_simples.png")
plt.savefig(out, dpi=220, facecolor="white", bbox_inches="tight")
print("saved", out)
