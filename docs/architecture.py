"""
BriefUp Agent Architecture Diagram
Publication-quality figure (NeurIPS/ICLR style)
Output: architecture.svg + architecture.png (300dpi)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm
import os

# ── 한글 폰트 설정 ─────────────────────────────────────────────
plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 색상 팔레트 ────────────────────────────────────────────────
C_ENTRY     = "#F1F5F9"
C_ORCH      = "#DBEAFE"
C_TOOLS     = "#DCFCE7"
C_EXT       = "#FEF9C3"
C_SESSION   = "#F3E8FF"
C_OBS       = "#FFE4E6"
C_BORDER    = "#94A3B8"
C_ARROW     = "#374151"
C_TEXT      = "#1E293B"
C_SUB       = "#6B7280"
C_DASH_BG   = "#F8FAFC"

fig, ax = plt.subplots(figsize=(16, 13))
ax.set_xlim(0, 16)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor("white")


# ── 헬퍼 ──────────────────────────────────────────────────────

def box(ax, x, y, w, h, color, label, sublabel="", fontsize=9.5,
        border=C_BORDER, lw=1.2, radius=0.25):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=border, linewidth=lw, zorder=3
    )
    ax.add_patch(rect)
    cy = y + h / 2
    if sublabel:
        ax.text(x + w / 2, cy + 0.13, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=C_TEXT, zorder=4)
        ax.text(x + w / 2, cy - 0.18, sublabel, ha="center", va="center",
                fontsize=7.5, color=C_SUB, zorder=4)
    else:
        ax.text(x + w / 2, cy, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=C_TEXT, zorder=4)


def layer_bg(ax, x, y, w, h, title, color=C_DASH_BG, border="#CBD5E1"):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.35",
        facecolor=color, edgecolor=border, linewidth=1.0,
        linestyle="--", zorder=1
    )
    ax.add_patch(rect)
    ax.text(x + 0.18, y + h - 0.22, title, ha="left", va="top",
            fontsize=8, color="#64748B", fontstyle="italic", zorder=4)


def arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW, lw=1.4, rad=0.0, ls="solid"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            linestyle=ls,
        ),
        zorder=5,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, ha="left", va="center",
                fontsize=7, color=C_SUB, fontstyle="italic", zorder=6)


def barrow(ax, x1, y1, x2, y2, label="", color=C_ARROW, lw=1.4):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color=color, lw=lw),
        zorder=5,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, ha="left", va="center",
                fontsize=7.5, color=C_SUB, fontstyle="italic", zorder=6)


# ═══════════════════════════════════════════════════════════════
# 제목
# ═══════════════════════════════════════════════════════════════
ax.text(8, 12.65,
        "BriefUp: Multi-Model Content Curation Agent Architecture",
        ha="center", va="center", fontsize=13.5, fontweight="bold", color=C_TEXT)
ax.text(8, 12.28,
        "Claude Haiku (Orchestration)  ·  GPT-5 (Generation)  ·  Cross-Model Verification",
        ha="center", va="center", fontsize=9, color=C_SUB)


# ═══════════════════════════════════════════════════════════════
# LAYER 0 — 진입점
# ═══════════════════════════════════════════════════════════════
layer_bg(ax, 0.3, 11.45, 10.8, 0.70, "Layer 0  ·  Entry Points")

box(ax, 0.65, 11.58, 3.0, 0.47, C_ENTRY, "Scheduler",
    sublabel="python -m agent.scheduler", fontsize=9)
box(ax, 4.20, 11.58, 3.5, 0.47, C_ENTRY, "REST API",
    sublabel="POST /api/content/run-pipeline", fontsize=9)
box(ax, 8.10, 11.58, 2.6, 0.47, C_ENTRY, "Manual Topics",
    sublabel="topics=[{name, category}]", fontsize=9)


# ═══════════════════════════════════════════════════════════════
# LAYER 1 — 오케스트레이션
# ═══════════════════════════════════════════════════════════════
layer_bg(ax, 0.3, 9.92, 10.8, 1.38, "Layer 1  ·  Orchestration")

box(ax, 0.65, 10.08, 10.0, 1.1, C_ORCH,
    "Claude Haiku 4.5 Agent   (agent_runner.py)",
    sublabel="MAX_ITERATIONS=50  ·  asyncio.gather (parallel execution)  ·  message history",
    fontsize=10.5, lw=1.8)

# 진입점 → 오케스트레이션
for xc in [2.15, 5.95, 9.40]:
    arrow(ax, xc, 11.58, xc, 11.18)


# ═══════════════════════════════════════════════════════════════
# LAYER 2 — 파이프라인 도구
# ═══════════════════════════════════════════════════════════════
layer_bg(ax, 0.3, 3.80, 10.8, 5.95,
         "Layer 2  ·  Pipeline Tools  (FastMCP in-process)")

# MCP 프로토콜 화살표
barrow(ax, 5.65, 10.08, 5.65, 9.75,
       label="MCP Protocol  (FastMCP)", lw=1.6)

# ── T1 ────────────────────────────────────────────────────────
box(ax, 0.65, 9.00, 4.5, 0.55, C_TOOLS,
    "T1 · get_active_topics()",
    sublabel="Fetch active user topics from DB", fontsize=9)
box(ax, 5.75, 9.00, 1.7, 0.55, C_EXT, "Supabase", fontsize=8.5)
arrow(ax, 5.15, 9.275, 5.75, 9.275)
ax.text(5.35, 9.43, "DB read", fontsize=7, color=C_SUB, fontstyle="italic")

# T1 ← 오케스트레이션
arrow(ax, 2.90, 10.08, 2.90, 9.55)

# ── T2 ────────────────────────────────────────────────────────
box(ax, 0.65, 7.80, 4.5, 0.65, C_TOOLS,
    "T2 · collect_articles()",
    sublabel="Parallel across topics  ·  cross-run URL dedup", fontsize=9)
arrow(ax, 2.90, 9.00, 2.90, 8.45)

box(ax, 5.75, 8.55, 2.3, 0.40, C_EXT, "arXiv API", fontsize=8.5)
box(ax, 5.75, 8.10, 2.3, 0.40, C_EXT, "RSS Feeds (by category)", fontsize=8)
box(ax, 5.75, 7.60, 2.3, 0.55, C_EXT, "Tavily Web Search",
    sublabel="trust_score ≥ 0.65", fontsize=8)
for ya, yb in [(8.10, 8.75), (8.10, 8.30), (8.10, 7.87)]:
    arrow(ax, 5.15, ya, 5.75, yb)

# ── T3 ────────────────────────────────────────────────────────
box(ax, 0.65, 6.55, 4.5, 0.65, C_TOOLS,
    "T3 · summarize_article()",
    sublabel="Parallel within same topic  ·  GPT-5 → Claude cross-verify", fontsize=9)
arrow(ax, 2.90, 7.80, 2.90, 7.20)

box(ax, 5.75, 6.70, 2.0, 0.38, C_EXT,  "GPT-5  (generate)", fontsize=8.5)
box(ax, 8.15, 6.70, 2.4, 0.38, C_ORCH, "Claude Haiku  (verify)", fontsize=8)
ax.annotate("", xy=(8.15, 6.89), xytext=(7.75, 6.89),
            arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=1.2), zorder=5)
ax.text(7.4, 6.57, "faithfulness ≥ 0.70", ha="center", va="top",
        fontsize=7, color=C_SUB, fontstyle="italic")
arrow(ax, 5.15, 6.87, 5.75, 6.89)

# ── T4 ────────────────────────────────────────────────────────
box(ax, 0.65, 5.35, 4.5, 0.65, C_TOOLS,
    "T4 · generate_quizzes()",
    sublabel="3 quizzes  ·  verified_count > 0 to proceed", fontsize=9)
arrow(ax, 2.90, 6.55, 2.90, 6.00)

box(ax, 5.75, 5.50, 2.0, 0.38, C_EXT,  "GPT-5  (generate)", fontsize=8.5)
box(ax, 8.15, 5.50, 2.4, 0.38, C_ORCH, "Claude Haiku  (cross-verify)", fontsize=8)
ax.annotate("", xy=(8.15, 5.69), xytext=(7.75, 5.69),
            arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=1.2), zorder=5)
ax.text(7.4, 5.37, "policy_rejected if all fail", ha="center", va="top",
        fontsize=7, color=C_SUB, fontstyle="italic")
arrow(ax, 5.15, 5.67, 5.75, 5.69)

# ── T5 ────────────────────────────────────────────────────────
box(ax, 0.65, 4.15, 4.5, 0.65, C_TOOLS,
    "T5 · save_content()",
    sublabel="contents + quizzes → Supabase", fontsize=9)
arrow(ax, 2.90, 5.35, 2.90, 4.80)

box(ax, 5.75, 4.30, 1.7, 0.45, C_EXT, "Supabase", fontsize=8.5)
arrow(ax, 5.15, 4.475, 5.75, 4.525)
ax.text(5.35, 4.78, "INSERT", fontsize=7, color=C_SUB, fontstyle="italic")


# ═══════════════════════════════════════════════════════════════
# SESSION STORE (오른쪽 플로팅)
# ═══════════════════════════════════════════════════════════════
layer_bg(ax, 11.3, 5.6, 4.38, 4.05,
         "Session Store", color="#FAF5FF", border="#A78BFA")

box(ax, 11.55, 9.05, 3.85, 0.45, C_SESSION,
    '_session["articles"]', fontsize=8.5, border="#A78BFA")

ax.text(11.65, 8.95,
        "article_id → {\n  title, text  ← full text (isolated)\n"
        "  source, url\n  summary?    ← after T3 pass\n"
        "  quizzes?    ← after T4 pass\n}",
        ha="left", va="top", fontsize=7.8, color=C_TEXT,
        fontfamily="monospace", linespacing=1.55, zorder=4)

box(ax, 11.55, 5.73, 3.85, 0.52, C_SESSION,
    "collect_step_orders",
    sublabel="parent-child span hierarchy (Observability)",
    fontsize=8.5, border="#A78BFA")

# collect → session (full text)
ax.annotate("", xy=(11.3, 8.85), xytext=(9.0, 8.12),
            arrowprops=dict(arrowstyle="-|>", color="#7C3AED", lw=1.2,
                            connectionstyle="arc3,rad=-0.3"), zorder=5)
ax.text(10.5, 8.65, "store full text", ha="center", va="bottom",
        fontsize=7, color="#7C3AED", fontstyle="italic")

# session → summarize (text_preview only)
ax.annotate("", xy=(5.15, 6.60), xytext=(11.3, 8.3),
            arrowprops=dict(arrowstyle="-|>", color="#7C3AED", lw=1.2,
                            connectionstyle="arc3,rad=0.22"), zorder=5)
ax.text(7.9, 7.5, "expose text_preview only\n(token isolation)",
        ha="center", va="center", fontsize=7, color="#7C3AED",
        fontstyle="italic")


# ═══════════════════════════════════════════════════════════════
# LAYER 3 — 관측 계층
# ═══════════════════════════════════════════════════════════════
layer_bg(ax, 0.3, 2.30, 10.8, 1.38, "Layer 3  ·  Observability")

box(ax, 0.65, 2.45, 4.8, 1.05, C_OBS,
    "PipelineLogger  (core/logger.py)",
    sublabel="pipeline_runs  ·  pipeline_logs  ·  failure_type  ·  cost_usd",
    fontsize=9.5, lw=1.4)

ax.text(6.0, 3.32, "failure_type classification:", ha="left", va="center",
        fontsize=8, fontweight="bold", color=C_TEXT)
failure_types = [
    ("technical",        "#EF4444"),
    ("policy_rejected",  "#F97316"),
    ("quality_rejected", "#EAB308"),
    ("not_found",        "#8B5CF6"),
]
for i, (ft, col) in enumerate(failure_types):
    ax.text(6.0 + i * 2.4, 2.95, f"● {ft}",
            ha="left", va="center", fontsize=7.5, color=col)

ax.text(6.0, 2.60,
        "quiz_pass_rate  ·  avg_faithfulness  ·  run_quality: success / partial / failed  ·  cost_usd",
        ha="left", va="center", fontsize=7.5, color=C_SUB)

# T5 → Observability
arrow(ax, 2.90, 4.15, 2.90, 3.50)

# 오케스트레이션 → 로거 (token 집계, 점선)
ax.annotate("", xy=(1.5, 3.50), xytext=(3.2, 10.08),
            arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=1.0,
                            connectionstyle="arc3,rad=0.42",
                            linestyle="dashed"), zorder=5)
ax.text(0.68, 6.8, "token\nusage", ha="center", va="center",
        fontsize=7, color=C_SUB, fontstyle="italic", rotation=85)


# ═══════════════════════════════════════════════════════════════
# 범례
# ═══════════════════════════════════════════════════════════════
legend_items = [
    (C_ORCH,    "Orchestration  (Claude Haiku 4.5)"),
    (C_TOOLS,   "Pipeline Tools  (MCP)"),
    (C_EXT,     "External APIs"),
    (C_SESSION, "Session Store  (Token Isolation)"),
    (C_OBS,     "Observability Layer"),
    (C_ENTRY,   "Entry Points"),
]
lx, ly = 11.45, 5.30
ax.text(lx, ly + 0.12, "Legend", ha="left", va="bottom",
        fontsize=8.5, fontweight="bold", color=C_TEXT)
for i, (col, label) in enumerate(legend_items):
    yi = ly - i * 0.43
    rect = FancyBboxPatch((lx, yi - 0.15), 0.33, 0.28,
                          boxstyle="round,pad=0,rounding_size=0.06",
                          facecolor=col, edgecolor=C_BORDER, linewidth=0.8, zorder=6)
    ax.add_patch(rect)
    ax.text(lx + 0.44, yi, label, ha="left", va="center",
            fontsize=8, color=C_TEXT, zorder=6)


# ═══════════════════════════════════════════════════════════════
# 저장
# ═══════════════════════════════════════════════════════════════
out_dir = os.path.dirname(os.path.abspath(__file__))
svg_path = os.path.join(out_dir, "architecture.svg")
png_path = os.path.join(out_dir, "architecture.png")

plt.tight_layout(pad=0.3)
fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
fig.savefig(png_path, format="png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()

print(f"SVG: {svg_path}")
print(f"PNG: {png_path}")
