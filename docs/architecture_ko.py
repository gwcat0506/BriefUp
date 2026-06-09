"""
BriefUp 에이전트 아키텍처 다이어그램 (한국어)
논문 수준 Figure — architecture_ko.svg / architecture_ko.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams["font.family"] = ["NanumSquare", "Apple SD Gothic Neo", "AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

C_ENTRY   = "#F1F5F9"; C_ORCH  = "#DBEAFE"; C_TOOLS = "#DCFCE7"
C_EXT     = "#FEF9C3"; C_SES   = "#F3E8FF"; C_OBS   = "#FFE4E6"
C_BDR     = "#94A3B8"; C_ARR   = "#374151"; C_TXT   = "#1E293B"
C_SUB     = "#6B7280"; C_DASH  = "#F8FAFC"

fig, ax = plt.subplots(figsize=(16, 13))
ax.set_xlim(0, 16); ax.set_ylim(0, 13); ax.axis("off")
fig.patch.set_facecolor("white")


def box(ax, x, y, w, h, fc, label, sub="", fs=9.5, bc=C_BDR, lw=1.2, r=0.25):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=bc, linewidth=lw, zorder=3))
    cy = y + h / 2
    if sub:
        ax.text(x+w/2, cy+0.13, label, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=C_TXT, zorder=4)
        ax.text(x+w/2, cy-0.18, sub, ha="center", va="center",
                fontsize=7.5, color=C_SUB, zorder=4)
    else:
        ax.text(x+w/2, cy, label, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=C_TXT, zorder=4)


def layer(ax, x, y, w, h, title, fc=C_DASH, bc="#CBD5E1"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.35",
        facecolor=fc, edgecolor=bc, linewidth=1.0, linestyle="--", zorder=1))
    ax.text(x+0.18, y+h-0.22, title, ha="left", va="top",
            fontsize=8, color="#64748B", fontstyle="italic", zorder=4)


def arr(ax, x1, y1, x2, y2, label="", color=C_ARR, lw=1.4, rad=0.0, ls="solid"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                        connectionstyle=f"arc3,rad={rad}", linestyle=ls), zorder=5)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.08, my, label, ha="left", va="center",
                fontsize=7, color=C_SUB, fontstyle="italic", zorder=6)


def barr(ax, x1, y1, x2, y2, label="", color=C_ARR, lw=1.4):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color=color, lw=lw), zorder=5)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.08, my, label, ha="left", va="center",
                fontsize=7.5, color=C_SUB, fontstyle="italic", zorder=6)


# ── 제목 ────────────────────────────────────────────────────────
ax.text(8, 12.65, "BriefUp: 멀티 모델 콘텐츠 큐레이션 에이전트 아키텍처",
        ha="center", va="center", fontsize=13, fontweight="bold", color=C_TXT)
ax.text(8, 12.28,
        "Claude Haiku (오케스트레이션)  ·  GPT-5 (콘텐츠 생성)  ·  교차 검증 (Cross-Model Verification)",
        ha="center", va="center", fontsize=9, color=C_SUB)

# ── 계층 0: 진입점 ────────────────────────────────────────────
layer(ax, 0.3, 11.45, 10.8, 0.70, "계층 0  ·  진입점")
box(ax, 0.65, 11.58, 3.0, 0.47, C_ENTRY, "스케줄러",
    sub="python -m agent.scheduler", fs=9)
box(ax, 4.20, 11.58, 3.5, 0.47, C_ENTRY, "REST API",
    sub="POST /api/content/run-pipeline", fs=9)
box(ax, 8.10, 11.58, 2.6, 0.47, C_ENTRY, "수동 토픽 지정",
    sub="topics=[{name, category}]", fs=9)

# ── 계층 1: 오케스트레이션 ───────────────────────────────────
layer(ax, 0.3, 9.92, 10.8, 1.38, "계층 1  ·  오케스트레이션")
box(ax, 0.65, 10.08, 10.0, 1.1, C_ORCH,
    "Claude Haiku 4.5 에이전트   (agent_runner.py)",
    sub="최대 반복 50회  ·  asyncio.gather (병렬 실행)  ·  대화 히스토리 관리",
    fs=10.5, lw=1.8)
for xc in [2.15, 5.95, 9.40]:
    arr(ax, xc, 11.58, xc, 11.18)

# ── 계층 2: 파이프라인 도구 ──────────────────────────────────
layer(ax, 0.3, 3.80, 10.8, 5.95,
      "계층 2  ·  파이프라인 도구  (FastMCP in-process)")
barr(ax, 5.65, 10.08, 5.65, 9.75, label="MCP 프로토콜  (FastMCP)", lw=1.6)

# T1
box(ax, 0.65, 9.00, 4.5, 0.55, C_TOOLS,
    "T1 · 활성 토픽 조회  get_active_topics()",
    sub="사용자 활성 관심사 목록 조회", fs=9)
box(ax, 5.75, 9.00, 1.7, 0.55, C_EXT, "Supabase", fs=8.5)
arr(ax, 5.15, 9.275, 5.75, 9.275)
ax.text(5.35, 9.43, "DB 읽기", fontsize=7, color=C_SUB, fontstyle="italic")
arr(ax, 2.90, 10.08, 2.90, 9.55)

# T2
box(ax, 0.65, 7.80, 4.5, 0.65, C_TOOLS,
    "T2 · 아티클 수집  collect_articles()",
    sub="토픽 병렬 처리  ·  크로스런 URL 중복 제거", fs=9)
arr(ax, 2.90, 9.00, 2.90, 8.45)

box(ax, 5.75, 8.55, 2.3, 0.40, C_EXT, "arXiv API (학술)", fs=8.5)
box(ax, 5.75, 8.10, 2.3, 0.40, C_EXT, "RSS 피드 (카테고리별)", fs=8)
box(ax, 5.75, 7.60, 2.3, 0.55, C_EXT, "Tavily 웹 검색",
    sub="신뢰도 점수 ≥ 0.65", fs=8)
for ya, yb in [(8.10, 8.75), (8.10, 8.30), (8.10, 7.87)]:
    arr(ax, 5.15, ya, 5.75, yb)

# T3
box(ax, 0.65, 6.55, 4.5, 0.65, C_TOOLS,
    "T3 · 요약 생성  summarize_article()",
    sub="동일 토픽 내 병렬 처리  ·  GPT-5 생성 → Claude 교차 검증", fs=9)
arr(ax, 2.90, 7.80, 2.90, 7.20)
box(ax, 5.75, 6.70, 2.0, 0.38, C_EXT,  "GPT-5  (요약 생성)", fs=8.5)
box(ax, 8.15, 6.70, 2.4, 0.38, C_ORCH, "Claude Haiku  (검증)", fs=8)
ax.annotate("", xy=(8.15, 6.89), xytext=(7.75, 6.89),
    arrowprops=dict(arrowstyle="-|>", color=C_ARR, lw=1.2), zorder=5)
ax.text(7.4, 6.57, "충실도 ≥ 0.70", ha="center", va="top",
        fontsize=7, color=C_SUB, fontstyle="italic")
arr(ax, 5.15, 6.87, 5.75, 6.89)

# T4
box(ax, 0.65, 5.35, 4.5, 0.65, C_TOOLS,
    "T4 · 퀴즈 생성  generate_quizzes()",
    sub="3문제 생성  ·  검증 통과 수 > 0 조건 충족 시 저장", fs=9)
arr(ax, 2.90, 6.55, 2.90, 6.00)
box(ax, 5.75, 5.50, 2.0, 0.38, C_EXT,  "GPT-5  (퀴즈 생성)", fs=8.5)
box(ax, 8.15, 5.50, 2.4, 0.38, C_ORCH, "Claude Haiku  (교차 검증)", fs=8)
ax.annotate("", xy=(8.15, 5.69), xytext=(7.75, 5.69),
    arrowprops=dict(arrowstyle="-|>", color=C_ARR, lw=1.2), zorder=5)
ax.text(7.4, 5.37, "전량 탈락 시 policy_rejected", ha="center", va="top",
        fontsize=7, color=C_SUB, fontstyle="italic")
arr(ax, 5.15, 5.67, 5.75, 5.69)

# T5
box(ax, 0.65, 4.15, 4.5, 0.65, C_TOOLS,
    "T5 · 콘텐츠 저장  save_content()",
    sub="요약 + 검증된 퀴즈 → Supabase 저장", fs=9)
arr(ax, 2.90, 5.35, 2.90, 4.80)
box(ax, 5.75, 4.30, 1.7, 0.45, C_EXT, "Supabase", fs=8.5)
arr(ax, 5.15, 4.475, 5.75, 4.525)
ax.text(5.35, 4.78, "INSERT", fontsize=7, color=C_SUB, fontstyle="italic")

# ── 세션 스토어 ────────────────────────────────────────────────
layer(ax, 11.3, 5.6, 4.38, 4.05, "세션 스토어", fc="#FAF5FF", bc="#A78BFA")
box(ax, 11.55, 9.05, 3.85, 0.45, C_SES,
    '_session["articles"]', fs=8.5, bc="#A78BFA")
ax.text(11.65, 8.95,
        "article_id → {\n  title, text  ← 원문 (격리 보관)\n"
        "  source, url\n  summary?    ← T3 통과 후 추가\n"
        "  quizzes?    ← T4 통과 후 추가\n}",
        ha="left", va="top", fontsize=7.8, color=C_TXT,
        linespacing=1.55, zorder=4)
box(ax, 11.55, 5.73, 3.85, 0.52, C_SES,
    "collect_step_orders",
    sub="부모-자식 스팬 계층 추적 (관측성)",
    fs=8.5, bc="#A78BFA")
ax.annotate("", xy=(11.3, 8.85), xytext=(9.0, 8.12),
    arrowprops=dict(arrowstyle="-|>", color="#7C3AED", lw=1.2,
                    connectionstyle="arc3,rad=-0.3"), zorder=5)
ax.text(10.5, 8.65, "원문 전체 저장", ha="center", va="bottom",
        fontsize=7, color="#7C3AED", fontstyle="italic")
ax.annotate("", xy=(5.15, 6.60), xytext=(11.3, 8.3),
    arrowprops=dict(arrowstyle="-|>", color="#7C3AED", lw=1.2,
                    connectionstyle="arc3,rad=0.22"), zorder=5)
ax.text(7.9, 7.5, "미리보기(300자)만 노출\n(토큰 격리)",
        ha="center", va="center", fontsize=7, color="#7C3AED", fontstyle="italic")

# ── 계층 3: 관측 계층 ─────────────────────────────────────────
layer(ax, 0.3, 2.30, 10.8, 1.38, "계층 3  ·  관측 계층 (Observability)")
box(ax, 0.65, 2.45, 4.8, 1.05, C_OBS,
    "PipelineLogger  (core/logger.py)",
    sub="pipeline_runs  ·  pipeline_logs  ·  실패 유형 분류  ·  비용(USD)",
    fs=9.5, lw=1.4)
ax.text(6.0, 3.32, "실패 유형 분류:", ha="left", va="center",
        fontsize=8, fontweight="bold", color=C_TXT)
for i, (ft, lbl, col) in enumerate([
    ("technical",       "기술 오류",    "#EF4444"),
    ("policy_rejected", "정책 거절",    "#F97316"),
    ("quality_rejected","품질 거절",    "#EAB308"),
    ("not_found",       "참조 없음",    "#8B5CF6"),
]):
    ax.text(6.0 + i*2.4, 2.95, f"● {ft}", ha="left", va="center",
            fontsize=7.5, color=col)
    ax.text(6.0 + i*2.4, 2.68, f"  ({lbl})", ha="left", va="center",
            fontsize=7, color=col)
ax.text(6.0, 2.42,
        "퀴즈 통과율  ·  평균 충실도  ·  실행 품질: 성공 / 부분 / 실패  ·  실행 비용",
        ha="left", va="center", fontsize=7.5, color=C_SUB)
arr(ax, 2.90, 4.15, 2.90, 3.50)
ax.annotate("", xy=(1.5, 3.50), xytext=(3.2, 10.08),
    arrowprops=dict(arrowstyle="-|>", color=C_ARR, lw=1.0,
                    connectionstyle="arc3,rad=0.42", linestyle="dashed"), zorder=5)
ax.text(0.68, 6.8, "토큰\n사용량", ha="center", va="center",
        fontsize=7, color=C_SUB, fontstyle="italic", rotation=85)

# ── 범례 ────────────────────────────────────────────────────────
legend = [
    (C_ORCH,  "오케스트레이션  (Claude Haiku 4.5)"),
    (C_TOOLS, "파이프라인 도구  (MCP)"),
    (C_EXT,   "외부 API"),
    (C_SES,   "세션 스토어  (토큰 격리)"),
    (C_OBS,   "관측 계층"),
    (C_ENTRY, "진입점"),
]
lx, ly = 11.45, 5.28
ax.text(lx, ly+0.12, "범례", ha="left", va="bottom",
        fontsize=8.5, fontweight="bold", color=C_TXT)
for i, (c, lbl) in enumerate(legend):
    yi = ly - i*0.43
    ax.add_patch(FancyBboxPatch((lx, yi-0.15), 0.33, 0.28,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=c, edgecolor=C_BDR, linewidth=0.8, zorder=6))
    ax.text(lx+0.44, yi, lbl, ha="left", va="center", fontsize=8, color=C_TXT, zorder=6)

# ── 저장 ────────────────────────────────────────────────────────
out = os.path.dirname(os.path.abspath(__file__))
plt.tight_layout(pad=0.3)
fig.savefig(f"{out}/architecture_ko.svg", format="svg", bbox_inches="tight", facecolor="white")
fig.savefig(f"{out}/architecture_ko.png", format="png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("저장 완료: architecture_ko.svg / architecture_ko.png")
