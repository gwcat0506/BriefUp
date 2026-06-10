"""
BriefUp Agent Architecture — 2-Phase Narrative Diagram
사용자 중심 흐름 + ReAct 루프 (Retry · Memory · Reflection)
Output: architecture.svg + architecture.png (300dpi)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 색상 ──────────────────────────────────────────────────────
C_BG       = "white"
C_PHASE1   = "#EFF6FF"   # 연파랑 — 설정
C_PHASE2   = "#F0FDF4"   # 연초록 — 에이전트 루프
C_PHASE3   = "#FAF5FF"   # 연보라 — 사용자 출력
C_CLAUDE   = "#DBEAFE"   # 파랑 — Claude
C_GPT      = "#DCFCE7"   # 초록 — GPT-5
C_TOOL     = "#FEF9C3"   # 노랑 — Tool 호출
C_MEMORY   = "#F3E8FF"   # 보라 — Memory
C_REFLECT  = "#FEF3C7"   # 황금 — Reflection
C_PASS     = "#BBF7D0"   # 진초록 — 통과
C_FAIL     = "#FECACA"   # 빨강 — 탈락
C_DIAMOND  = "#FDE68A"   # 다이아몬드
C_BORDER   = "#94A3B8"
C_TEXT     = "#1E293B"
C_SUB      = "#64748B"
BLUE       = "#2563EB"
GREEN      = "#16A34A"
PURPLE     = "#7C3AED"
AMBER      = "#D97706"
RED        = "#DC2626"

fig, ax = plt.subplots(figsize=(22, 16))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis("off")
fig.patch.set_facecolor(C_BG)


# ── 헬퍼 ──────────────────────────────────────────────────────

def rbox(ax, x, y, w, h, fc, label, sub="", fs=9.5, bc=C_BORDER,
         lw=1.3, r=0.25, bold=True, sub_fs=8.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=bc, linewidth=lw, zorder=3))
    cy = y + h / 2
    fw = "bold" if bold else "normal"
    if sub:
        ax.text(x+w/2, cy+0.18, label, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=C_TEXT, zorder=4)
        ax.text(x+w/2, cy-0.20, sub, ha="center", va="center",
                fontsize=sub_fs, color=C_SUB, zorder=4)
    else:
        ax.text(x+w/2, cy, label, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=C_TEXT, zorder=4)


def diamond(ax, cx, cy, hw, hh, fc=C_DIAMOND, bc=AMBER, label="", fs=8.0):
    xs = [cx, cx+hw, cx, cx-hw, cx]
    ys = [cy+hh, cy, cy-hh, cy, cy+hh]
    ax.fill(xs, ys, facecolor=fc, edgecolor=bc, linewidth=1.4, zorder=3)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=C_TEXT, zorder=4)


def arr(ax, x1, y1, x2, y2, color=C_TEXT, lw=1.5, rad=0.0, ls="solid", label="", label_dx=0.1):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                        connectionstyle=f"arc3,rad={rad}", linestyle=ls), zorder=5)
    if label:
        mx, my = (x1+x2)/2 + label_dx, (y1+y2)/2
        ax.text(mx, my, label, ha="left", va="center",
                fontsize=7.5, color=color, fontstyle="italic", zorder=6)


def phase_bg(ax, x, y, w, h, color, border, label, label_color):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.4",
        facecolor=color, edgecolor=border, linewidth=1.5,
        linestyle="--", zorder=1))
    ax.text(x+0.22, y+h-0.18, label, ha="left", va="top",
            fontsize=9.5, fontweight="bold", color=label_color, zorder=4)


def badge(ax, x, y, text, color, fs=7.5):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color="white", zorder=7,
            bbox=dict(boxstyle="round,pad=0.28", facecolor=color, edgecolor="none"))


def num_badge(ax, x, y, n, color=BLUE):
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8.5,
            fontweight="bold", color="white", zorder=8,
            bbox=dict(boxstyle="circle,pad=0.25", facecolor=color, edgecolor="none"))


def pill_tag(ax, x, y, text, color, fs=7.5):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color="white", fontweight="bold", zorder=6,
            bbox=dict(boxstyle="round,pad=0.22", facecolor=color, edgecolor="none"))


# ═══════════════════════════════════════════════════════════════
# 제목
# ═══════════════════════════════════════════════════════════════
ax.text(11, 15.62, "BriefUp: Adaptive Multi-Model Content Curation Agent",
        ha="center", va="center", fontsize=15, fontweight="bold", color=C_TEXT)
ax.text(11, 15.24,
        "ReAct Loop  ·  Adaptive Retry  ·  Cross-run Memory  ·  Cross-Model Verification  ·  Reflection",
        ha="center", va="center", fontsize=9.5, color=C_SUB)


# ═══════════════════════════════════════════════════════════════
# PHASE 1 — 일회성 설정 (좌측)
# ═══════════════════════════════════════════════════════════════
phase_bg(ax, 0.3, 1.2, 4.2, 13.8, C_PHASE1, BLUE, "Phase 1  ·  일회성 설정", BLUE)

# 사용자
ax.text(2.4, 14.58, "[User]", ha="center", va="center", fontsize=10,
        fontweight="bold", color=BLUE, zorder=4)
rbox(ax, 0.8, 13.9, 3.2, 0.55, C_CLAUDE, "관심사 입력",
     sub='"AI/ML 배우고 싶어"', fs=9.5, bc=BLUE)

arr(ax, 2.4, 13.9, 2.4, 13.35)

rbox(ax, 0.8, 12.75, 3.2, 0.55, C_TOOL, "토픽 분류",
     sub="classifier.py", fs=9.5, bc=AMBER)

arr(ax, 2.4, 12.75, 2.4, 12.20)

# 커리큘럼 설계
rbox(ax, 0.8, 11.15, 3.2, 1.0, C_CLAUDE,
     "Claude: 커리큘럼 설계",
     sub="curriculum_gen.py", fs=9.5, bc=BLUE, lw=2.0)
ax.text(2.4, 11.55, "챕터 1 → 2 → 3 → ...", ha="center", va="center",
        fontsize=8.0, color=C_SUB)

arr(ax, 2.4, 11.15, 2.4, 10.60)

rbox(ax, 0.8, 10.05, 3.2, 0.50, C_PASS, "학습 로드맵 완성", fs=9.5, bc=GREEN)

# 구분선
ax.plot([0.3, 4.5], [9.75, 9.75], color="#CBD5E1", lw=1.2, linestyle=":")
ax.text(2.4, 9.50, "매일 자동 실행 ↓", ha="center", va="center",
        fontsize=8.0, color=C_SUB, fontstyle="italic")

arr(ax, 2.4, 10.05, 2.4, 9.20)

rbox(ax, 0.8, 8.55, 3.2, 0.60, C_TOOL, "스케줄러 (매일 자동)",
     sub="python -m agent.scheduler", fs=9.5, bc=AMBER)

# 스케줄러 → Phase 2 연결 화살표
arr(ax, 4.5, 8.85, 5.0, 8.85, color=BLUE, lw=2.0)


# ═══════════════════════════════════════════════════════════════
# PHASE 2 — Agent Loop (중앙 우측)
# ═══════════════════════════════════════════════════════════════
phase_bg(ax, 4.8, 1.2, 12.4, 13.8, C_PHASE2, GREEN, "Phase 2  ·  매일 자동 실행  —  ReAct Loop", GREEN)

# ── Memory 박스 (상단) ─────────────────────────────────────────
rbox(ax, 5.3, 13.75, 11.4, 0.88, C_MEMORY,
     "Cross-run Memory  —  이전 실행 기록",
     sub="충실도 · 퀴즈통과율 · 비용 · 지난 반성 · 다음 제안",
     fs=10.0, bc=PURPLE, lw=2.0)

arr(ax, 11.0, 13.75, 11.0, 13.30, color=PURPLE, lw=1.8,
    label="컨텍스트 주입", label_dx=0.1)

# ① 챕터 결정
num_badge(ax, 5.65, 12.85, "①")
rbox(ax, 5.9, 12.53, 5.0, 0.65, C_TOOL,
     "오늘의 챕터 결정",
     sub="get_collection_plan()  ·  커리큘럼 진도 추적", fs=9.5, bc=AMBER)

arr(ax, 8.4, 12.53, 8.4, 12.0, color=GREEN, lw=1.8)

# ② 아티클 수집
num_badge(ax, 5.65, 11.60, "②")
rbox(ax, 5.9, 11.28, 5.0, 0.65, C_TOOL,
     "아티클 수집",
     sub="collect_articles()  ·  arXiv · RSS · Tavily 웹검색", fs=9.5, bc=AMBER)

# 소스 태그
for i, (tag, color) in enumerate([("arXiv", "#3B82F6"), ("웹검색", "#8B5CF6"), ("RSS", "#059669")]):
    pill_tag(ax, 11.6, 11.77 - i*0.35, tag, color, fs=7.8)

arr(ax, 8.4, 11.28, 8.4, 10.65, color=GREEN, lw=1.8)

# ── 다이아몬드: 수집 충분? ─────────────────────────────────────
diamond(ax, 8.4, 10.28, 1.1, 0.38, label="수집 충분?\n(≥ 3개)", fs=7.8)

# YES → 아래
arr(ax, 8.4, 9.90, 8.4, 9.45, color=GREEN, lw=1.8)
badge(ax, 8.4, 9.68, "YES", GREEN, fs=7.5)

# NO → retry 화살표 (오른쪽 돌아 위로)
ax.annotate("", xy=(8.4, 11.28), xytext=(10.8, 10.28),
    arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5,
                    connectionstyle="arc3,rad=-0.3", linestyle="dashed"), zorder=5)
ax.text(10.85, 10.78, "🔄 검색어 조정 후\n재시도 (최대 1회)", ha="left", va="center",
        fontsize=7.8, color=RED, fontstyle="italic", zorder=6)
badge(ax, 10.5, 10.28, "NO / retry", RED, fs=7.5)

# ③ Cross-Model Verification 박스
num_badge(ax, 5.65, 9.05, "③")
ax.add_patch(FancyBboxPatch((5.9, 7.35), 10.8, 2.0,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F8FAFC", edgecolor=BLUE, linewidth=1.8, zorder=2))
ax.text(11.3, 9.17, "Cross-Model Verification", ha="center", va="center",
        fontsize=9.5, fontweight="bold", color=BLUE, zorder=4)

# 행 A: 요약
rbox(ax, 6.1, 8.60, 3.2, 0.58, C_GPT, "GPT-4o-mini: 요약 생성",
     sub="summarize_article()", fs=9.0, bc=GREEN, lw=1.5)
arr(ax, 9.3, 8.89, 10.1, 8.89, color=C_TEXT, lw=1.4)
rbox(ax, 10.1, 8.60, 3.6, 0.58, C_CLAUDE, "Claude: 충실도 검증",
     sub="faithfulness ≥ 0.70", fs=9.0, bc=BLUE, lw=1.5)
arr(ax, 13.7, 8.89, 14.4, 9.15, color=GREEN, lw=1.3)
rbox(ax, 14.4, 8.72, 1.9, 0.45, C_PASS, "✓ 통과", fs=8.5, bc=GREEN)
arr(ax, 13.7, 8.89, 14.4, 8.62, color=RED, lw=1.3)
rbox(ax, 14.4, 8.45, 1.9, 0.45, C_FAIL, "✗ 탈락", fs=8.5, bc=RED)

# 행 B: 퀴즈
rbox(ax, 6.1, 7.48, 3.2, 0.58, C_GPT, "GPT-4o-mini: 퀴즈 생성",
     sub="generate_quizzes()", fs=9.0, bc=GREEN, lw=1.5)
arr(ax, 9.3, 7.77, 10.1, 7.77, color=C_TEXT, lw=1.4)
rbox(ax, 10.1, 7.48, 3.6, 0.58, C_CLAUDE, "Claude: 퀴즈 검증",
     sub="verified_count > 0", fs=9.0, bc=BLUE, lw=1.5)
arr(ax, 13.7, 7.77, 14.4, 8.03, color=GREEN, lw=1.3)
arr(ax, 13.7, 7.77, 14.4, 7.50, color=RED, lw=1.3)

arr(ax, 8.4, 7.35, 8.4, 6.88, color=GREEN, lw=1.8)

# ④ 저장
num_badge(ax, 5.65, 6.50, "④")
rbox(ax, 5.9, 6.18, 5.0, 0.65, C_PASS,
     "검증된 콘텐츠 저장",
     sub="save_content()  ·  요약 + 퀴즈 → DB", fs=9.5, bc=GREEN, lw=1.8)

arr(ax, 8.4, 6.18, 8.4, 5.65, color=AMBER, lw=1.8)

# ⑤ Reflection
num_badge(ax, 5.65, 5.27, "⑤")
rbox(ax, 5.9, 4.95, 5.0, 0.65, C_REFLECT,
     "Claude: 실행 반성 (Reflection)",
     sub="save_reflection()  ·  품질 평가 + 다음 전략 메모", fs=9.5, bc=AMBER, lw=2.0)

# Reflection → Memory 피드백 화살표
ax.annotate("", xy=(16.2, 13.75), xytext=(16.2, 4.95),
    arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.8,
                    connectionstyle="arc3,rad=0.0", linestyle="dashed"), zorder=5)
ax.text(16.40, 9.35, "다음 실행에\n반영", ha="left", va="center",
        fontsize=8.0, color=PURPLE, fontstyle="italic", zorder=6)
ax.plot([10.9, 16.2], [5.275, 5.275], color=PURPLE, lw=1.8,
        linestyle="dashed", zorder=5)
ax.plot([16.2, 16.2], [5.275, 14.19], color=PURPLE, lw=1.8,
        linestyle="dashed", zorder=5)
ax.annotate("", xy=(16.7, 14.19), xytext=(16.2, 14.19),
    arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.8), zorder=5)


# ═══════════════════════════════════════════════════════════════
# PHASE 3 — 사용자 출력 (하단)
# ═══════════════════════════════════════════════════════════════
phase_bg(ax, 0.3, 0.18, 16.9, 0.95, C_PHASE3, PURPLE, "", PURPLE)

ax.text(0.6, 0.88, "Phase 3  ·  사용자 수신", ha="left", va="center",
        fontsize=9.5, fontweight="bold", color=PURPLE)

output_cards = [
    (1.8,  "오늘의 브리핑"),
    (6.2,  "퀴즈 3문제"),
    (10.6, "개념 레벨업"),
    (14.5, "스트릭"),
]
for cx, label in output_cards:
    rbox(ax, cx, 0.25, 3.5, 0.58, C_PHASE3, label, fs=9.5, bc=PURPLE, lw=1.4)

# Phase 2 → Phase 3 화살표
arr(ax, 8.4, 4.95, 8.4, 1.20, color=PURPLE, lw=1.8)


# ═══════════════════════════════════════════════════════════════
# 범례
# ═══════════════════════════════════════════════════════════════
legend_items = [
    (C_CLAUDE,  BLUE,   "Claude (Orchestrator + Verifier)"),
    (C_GPT,     GREEN,  "GPT-5 (Generator)"),
    (C_TOOL,    AMBER,  "Tool 호출"),
    (C_MEMORY,  PURPLE, "Cross-run Memory"),
    (C_REFLECT, AMBER,  "Reflection"),
    (C_DIAMOND, AMBER,  "Decision Point"),
]
lx = 17.3
ly = 14.5
ax.text(lx + 1.5, ly + 0.55, "Legend", ha="center", va="bottom",
        fontsize=9.5, fontweight="bold", color=C_TEXT)
for i, (fc, bc, label) in enumerate(legend_items):
    yi = ly - i * 0.65
    ax.add_patch(FancyBboxPatch((lx, yi - 0.18), 0.42, 0.34,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=fc, edgecolor=bc, linewidth=1.0, zorder=6))
    ax.text(lx + 0.58, yi, label, ha="left", va="center",
            fontsize=8.5, color=C_TEXT, zorder=6)

# 점선 = 피드백 루프 범례
ax.plot([lx, lx + 0.42], [ly - 4.3, ly - 4.3],
        color=PURPLE, lw=1.8, linestyle="dashed", zorder=6)
ax.text(lx + 0.58, ly - 4.3, "Feedback Loop", ha="left", va="center",
        fontsize=8.5, color=C_TEXT, zorder=6)
ax.plot([lx, lx + 0.42], [ly - 4.95, ly - 4.95],
        color=RED, lw=1.8, linestyle="dashed", zorder=6)
ax.text(lx + 0.58, ly - 4.95, "Retry Arrow", ha="left", va="center",
        fontsize=8.5, color=C_TEXT, zorder=6)


# ═══════════════════════════════════════════════════════════════
# 저장
# ═══════════════════════════════════════════════════════════════
out_dir = os.path.dirname(os.path.abspath(__file__))
svg_path = os.path.join(out_dir, "architecture.svg")
png_path = os.path.join(out_dir, "architecture.png")

plt.tight_layout(pad=0.3)
fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor=C_BG)
fig.savefig(png_path, format="png", dpi=300, bbox_inches="tight", facecolor=C_BG)
plt.close()

print(f"SVG: {svg_path}")
print(f"PNG: {png_path}")
