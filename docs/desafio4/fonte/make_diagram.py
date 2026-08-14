# -*- coding: utf-8 -*-
"""Gera o diagrama de arquitetura do CSV Insight (backend real) como PNG."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path as MplPath

NAVY = "#17324A"
BLUE = "#2E6C9E"
LIGHT_BLUE = "#EAF2F8"
MID = "#4A90C4"
GRAY = "#5B6770"
WHITE = "#FFFFFF"

fig, ax = plt.subplots(figsize=(8.6, 10.4))
ax.set_xlim(0, 10)
ax.set_ylim(1.85, 13.2)
ax.axis("off")

def box(x, y, w, h, text, fc=WHITE, ec=NAVY, tc=NAVY, fs=10.5, weight="bold", lw=1.6):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fs, color=tc, weight=weight, zorder=3, linespacing=1.35)
    return (x, y, w, h)

def vline(b1, b2, label=None, dashed=False, color=NAVY, lw=1.8):
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    start = (x1 + w1 / 2, y1)
    end = (x2 + w2 / 2, y2 + h2)
    arrow = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=14,
        linewidth=lw, color=color, zorder=1,
        linestyle=(0, (4, 3)) if dashed else "solid",
    )
    ax.add_patch(arrow)
    if label:
        ax.text((start[0] + end[0]) / 2 + 0.18, (start[1] + end[1]) / 2 - 0.19, label,
                 fontsize=8, color=GRAY, ha="left", va="center", style="italic")

def hline(b1, b2, label=None, color=BLUE, lw=1.8, dashed=False):
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    start = (x1 + w1, y1 + h1 / 2)
    end = (x2, y2 + h2 / 2)
    arrow = FancyArrowPatch(
        start, end, arrowstyle="<|-|>", mutation_scale=13,
        linewidth=lw, color=color, zorder=1,
        linestyle=(0, (4, 3)) if dashed else "solid",
    )
    ax.add_patch(arrow)
    if label:
        ax.text((start[0] + end[0]) / 2, start[1] + 0.22, label,
                 fontsize=8, color=GRAY, ha="center", va="bottom", style="italic")

# Title
ax.text(5, 12.85, "CSV Insight — arquitetura da solução (Desafio 4)",
        ha="center", va="center", fontsize=13.5, color=NAVY, weight="bold")

W = 4.6
X = 2.7

usuario   = box(X, 11.55, W, 0.65, "Usuário", fc=LIGHT_BLUE, fs=11)
frontend  = box(X, 10.55, W, 0.75, "Front-end\nReact + Vite + Chakra UI\n(Interface A: upload · Interface B: consulta)", fs=9.3)
fastapi   = box(X, 9.55, W, 0.7, "FastAPI — routes/\ndatasets.py · analyze.py", fs=9.6)
agentsvc  = box(X, 8.55, W, 0.7, "AgentService\n(services/agent_service.py)", fs=9.8)
agent     = box(X, 7.4, W, 0.85, "Agente Pydantic AI\n(agents/data_agent.py)\ndecide quais tools chamar", fs=9.4)

groq = box(8.05, 7.4, 1.75, 0.85, "Groq\nmodelo\nGPT-OSS", fc=NAVY, tc=WHITE, fs=9)

tools     = box(X, 6.15, W, 0.75, "5 tools tipadas\nlistar_colunas · obter_resumo · buscar_registros\nfiltrar_dados · calcular_estatisticas", fs=8.6)
datasvc   = box(X, 5.15, W, 0.65, "DatasetService\n(services/dataset_service.py)", fs=9.6)
store     = box(X, 4.05, W, 0.75, "Store em memória\ndataset processado + histórico\n(por processo, sem banco de dados)", fs=9)

vline(usuario, frontend)
vline(frontend, fastapi, label="POST /api/datasets\nPOST .../questions")
vline(fastapi, agentsvc)
vline(agentsvc, agent, label="agent.run_sync(pergunta)")
hline(agent, groq)
ax.text((agent[0] + agent[2] + groq[0]) / 2, agent[1] + agent[3] / 2 + 0.22, "tool\ncalling",
        fontsize=7.6, color=GRAY, ha="center", va="bottom", style="italic")
vline(agent, tools, label="@agent.tool")
vline(tools, datasvc, label="delega")
vline(datasvc, store, label="lê / consulta")

# Return path (resposta) — dashed, on the left
ret_x = X - 0.55
ax.plot([ret_x, ret_x], [4.4, 11.85], color=MID, lw=1.6, linestyle=(0, (4, 3)), zorder=1)
ax.annotate("", xy=(X, 11.87), xytext=(ret_x, 11.85),
            arrowprops=dict(arrowstyle="-|>", color=MID, lw=1.6))
ax.plot([ret_x, X], [4.4, 4.4], color=MID, lw=1.6, linestyle=(0, (4, 3)))
ax.text(ret_x - 0.12, 8.1, "resposta em texto (TextQueryResult)\nsobe de volta até o usuário",
        rotation=90, ha="center", va="center", fontsize=7.8, color=MID, style="italic")

# Upload ingestion side note
ing = box(0.15, 9.45, 2.15, 0.9, "Ingestão do ZIP/CSV\nDatasetUploadService\n+ DataCleaningService", fc=LIGHT_BLUE, fs=7.8, weight="normal")
ax.annotate("", xy=(X, 9.9), xytext=(2.3, 9.9),
            arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.3))
ax.text(1.2, 8.9, "grava em", fontsize=7.2, color=GRAY, ha="center", style="italic")
ax.annotate("", xy=(X - 0.05, 4.4), xytext=(1.2, 9.4),
            arrowprops=dict(arrowstyle="-", color=GRAY, lw=0, linestyle="dotted"))
ax.plot([1.2, 1.2], [4.4, 9.45], color=GRAY, lw=1.1, linestyle="dotted", zorder=1)
ax.plot([1.2, X], [4.4, 4.4], color=GRAY, lw=1.1, linestyle="dotted", zorder=1)
ax.annotate("", xy=(X - 0.02, 4.42), xytext=(1.25, 4.4),
            arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.1))

ax.text(5, 3.55,
        "Fluxo principal (linhas cheias): usuário → front-end → FastAPI → AgentService → agente → tools → dados.\n"
        "Retorno (linha tracejada azul): a resposta do agente sobe pela mesma cadeia até a interface de consulta.\n"
        "Ingestão (linha pontilhada cinza): o upload processa e grava o dataset diretamente no store em memória.",
        ha="center", va="top", fontsize=8, color=GRAY, linespacing=1.6)

plt.tight_layout()
import os
base = os.environ.get("REPORT_ASSETS_DIR", ".")
out = os.path.join(base, "arquitetura.png")
plt.savefig(out, dpi=220, facecolor="white", bbox_inches="tight")
print("saved", out)
