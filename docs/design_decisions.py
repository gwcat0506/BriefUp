"""
BriefUp 설계 결정 다이어그램 (논문 Figure 스타일)
핵심 설계 근거 3가지를 한 장에 시각화
Output: design_decisions.svg / design_decisions.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np
import os

plt.rcParams["font.family"] = ["NanumSquare", "Apple SD Gothic Neo", "AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 색상 ──────────────────────────────────────────────────────
C_CLAUDE  = "#DBEAFE"   # Claude — 파란
C_GPT     = "#DCFCE7"   # GPT-5 — 초록
C_GATE    = "#FEF9C3"   # 품질 게이트 — 노랑
C_PASS    = "#BBF7D0"   # 통과 — 진초록
C_FAIL    = "#FECACA"   # 탈락 — 빨강
C_SES     = "#F3E8FF"   # 세션 스토어 — 보라
C_BDR     = "#94A3B8"
C_TXT     = "#1E293B"
C_SUB     = "#6B7280"
C_HL      = "#0F172A"   # 강조 텍스트 (거의 검정)
RED       = "#EF4444"
GREEN     = "#16A34A"
BLUE      = "#2563EB"
PURPLE    = "#7C3AED"
ORANGE    = "#EA580C"

fig = plt.figure(figsize=(21, 13))
fig.patch.set_facecolor("white")

# 3개 서브플롯 (논문 Figure A/B/C)
axes = fig.subplots(1, 3, gridspec_kw={"width_ratios": [1.1, 1.1, 0.9],
                                        "wspace": 0.12})
for ax in axes:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis("off")

# ── 공통 헬퍼 ─────────────────────────────────────────────────

def box(ax, x, y, w, h, fc, label, sub="", fs=10.0, bc=C_BDR,
        lw=1.3, r=0.3, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=bc, linewidth=lw, zorder=3))
    cy = y + h / 2
    fw = "bold" if bold else "normal"
    if sub:
        ax.text(x+w/2, cy+0.18, label, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=C_TXT, zorder=4)
        ax.text(x+w/2, cy-0.22, sub, ha="center", va="center",
                fontsize=8.0, color=C_SUB, zorder=4)
    else:
        ax.text(x+w/2, cy, label, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=C_TXT, zorder=4)


def arr(ax, x1, y1, x2, y2, color=C_TXT, lw=1.6, rad=0.0, ls="solid"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                        connectionstyle=f"arc3,rad={rad}",
                        linestyle=ls), zorder=5)


def callout(ax, x, y, text, color="#0F172A", fs=8.0, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs,
            color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor=color, linewidth=0.8, alpha=0.95))


def badge(ax, x, y, text, color, fs=7.8):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color="white", zorder=7,
            bbox=dict(boxstyle="round,pad=0.30", facecolor=color,
                      edgecolor="none"))


def section_title(ax, x, y, letter, title, subtitle=""):
    ax.text(x, y+0.48, letter, ha="left", va="center",
            fontsize=17, fontweight="bold", color=BLUE, zorder=5)
    ax.text(x+0.75, y+0.52, title, ha="left", va="center",
            fontsize=12.5, fontweight="bold", color=C_HL, zorder=5)
    if subtitle:
        ax.text(x+0.75, y+0.10, subtitle, ha="left", va="center",
                fontsize=8.5, color=C_SUB, zorder=5)
    ax.axhline(y=y-0.05, xmin=0.02, xmax=0.98, color="#E2E8F0", lw=1.2)


# ═══════════════════════════════════════════════════════════════
# Figure A — 이중 모델 역할 분리 + 교차 검증
# ═══════════════════════════════════════════════════════════════
ax = axes[0]

section_title(ax, 0.3, 11.6,
              "(A)", "이중 모델 역할 분리",
              "역할별 최적 모델 선택 + 교차 검증")

# ── 두 모델 박스 (중앙) ────────────────────────────────────────
box(ax, 0.4, 9.2, 4.0, 1.7, C_CLAUDE,
    "Claude Haiku 4.5",
    sub="오케스트레이션 + 검증",
    fs=10.5, bc=BLUE, lw=2.0)
ax.text(2.4, 10.22, "역할", ha="center", fontsize=8, color=BLUE, fontstyle="italic")
ax.text(2.4, 9.88, "① 에이전트 루프 제어\n② 요약 faithfulness 검증\n③ 퀴즈 교차 검증",
        ha="center", va="center", fontsize=8.5, color=C_TXT, linespacing=1.7)
# 비용 배지 — 우측 상단
badge(ax, 3.95, 10.75, "$1/1M tokens", BLUE, fs=7.5)

box(ax, 5.4, 9.2, 4.2, 1.7, C_GPT,
    "GPT-5",
    sub="콘텐츠 생성 전담",
    fs=10.5, bc=GREEN, lw=2.0)
ax.text(7.5, 10.22, "역할", ha="center", fontsize=8, color=GREEN, fontstyle="italic")
ax.text(7.5, 9.88, "① 아티클 요약 생성\n② 퀴즈 3문제 생성\n③ 토픽 분류",
        ha="center", va="center", fontsize=8.5, color=C_TXT, linespacing=1.7)
# 비용 배지 — 우측 상단
badge(ax, 9.15, 10.75, "$15/1M tokens", GREEN, fs=7.5)

# ── 교차 검증 루프 ─────────────────────────────────────────────
box(ax, 0.8, 7.35, 3.4, 0.70, C_GPT,
    "GPT-5: 요약/퀴즈 생성", fs=9.0, bc=GREEN, lw=1.5)
box(ax, 5.5, 7.35, 3.6, 0.70, C_CLAUDE,
    "Claude: 검증 판정", fs=9.0, bc=BLUE, lw=1.5)

arr(ax, 4.2, 7.70, 5.5, 7.70, color=C_TXT, lw=1.6)
ax.text(4.85, 7.90, "검증 요청", ha="center", fontsize=8.0,
        color=C_SUB, fontstyle="italic")

# 통과/탈락 분기
arr(ax, 7.3, 7.35, 7.3, 6.50,  color=GREEN, lw=1.6)   # 통과
arr(ax, 5.8, 7.35, 4.4, 6.50,  color=RED,   lw=1.6)   # 탈락

box(ax, 5.8, 5.85, 2.7, 0.60, C_PASS, "저장 진행", fs=9.0, bc=GREEN, lw=1.5)
box(ax, 2.8, 5.85, 2.7, 0.60, C_FAIL, "스킵 (탈락)", fs=9.0, bc=RED,   lw=1.5)
badge(ax, 7.15, 6.35, "PASS", GREEN, fs=7.5)
badge(ax, 5.50, 6.35, "FAIL", RED,   fs=7.5)

ax.text(7.15, 5.68, "faithfulness ≥ 0.70\n검증 통과 수 > 0",
        ha="center", fontsize=8.0, color=GREEN, linespacing=1.5)
ax.text(4.15, 5.68, "failure_type =\npolicy_rejected",
        ha="center", fontsize=8.0, color=RED, linespacing=1.5)

# 모델 박스 → 검증 루프 연결
arr(ax, 2.4, 9.2, 2.4, 8.05, color=GREEN, lw=1.2, ls="dashed")
arr(ax, 7.5, 9.2, 7.5, 8.05, color=BLUE,  lw=1.2, ls="dashed")

# 설계 근거 박스 ─────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 3.85), 9.4, 1.65,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F0FDF4", edgecolor=GREEN, linewidth=1.2,
    linestyle="--", zorder=2))
ax.text(0.6, 5.28, "설계 근거", fontsize=9.0, fontweight="bold", color=GREEN)
ax.text(0.6, 4.88,
        "• 동일 모델이 생성과 검증을 모두 하면 같은 오류를 반복 (Blind Spot)",
        fontsize=8.5, color=C_TXT, linespacing=1.5)
ax.text(0.6, 4.45,
        "• Claude Haiku: Tool Use 지시 이해에 강함 → 에이전트 역할 최적",
        fontsize=8.5, color=C_TXT)
ax.text(0.6, 4.07,
        "• GPT-5: 한국어 생성 품질 + 구조화 출력에 강함 → 생성 역할 최적",
        fontsize=8.5, color=C_TXT)


# ═══════════════════════════════════════════════════════════════
# Figure B — 세션 스토어 토큰 격리
# ═══════════════════════════════════════════════════════════════
ax = axes[1]

section_title(ax, 0.3, 11.6,
              "(B)", "세션 스토어 토큰 격리",
              "원문을 Claude에 직접 노출하지 않는 이유")

# ── 문제 상황 (Without) ────────────────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 9.0), 9.4, 2.2,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#FFF1F2", edgecolor=RED, linewidth=1.2, zorder=2))
ax.text(0.6, 10.98, "문제: 원문 직접 전달 시", fontsize=9.0,
        fontweight="bold", color=RED)

box(ax, 0.5, 9.8, 2.8, 0.80, "#FEE2E2",
    "원문 전체\n(~3,000 tokens)", fs=8.5, bc=RED, lw=1.2, bold=False)
arr(ax, 3.3, 10.20, 4.1, 10.20, color=RED, lw=1.6)
box(ax, 4.1, 9.8, 2.5, 0.80, C_CLAUDE,
    "Claude Haiku\n에이전트", fs=9.0, bc=BLUE, lw=1.5)
arr(ax, 6.6, 10.20, 7.2, 10.20, color=RED, lw=1.6)
box(ax, 7.2, 9.8, 2.3, 0.80, "#FEE2E2",
    "토큰 폭증\n할루시네이션", fs=8.5, bc=RED, lw=1.2, bold=False)

ax.text(3.7, 9.62, "N articles × 3,000 tokens", ha="center",
        fontsize=8.0, color=RED)
ax.text(3.7, 9.30, "→ Claude 비용 수십 배 증가", ha="center",
        fontsize=8.5, color=RED, fontweight="bold")

# ── 해결책 (With Session Store) ───────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 6.10), 9.4, 2.65,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F0FDF4", edgecolor=GREEN, linewidth=1.5, zorder=2))
ax.text(0.6, 8.52, "해결: 세션 스토어 격리", fontsize=9.0,
        fontweight="bold", color=GREEN)

# 수집 → 세션 저장 (원문)
box(ax, 0.5, 6.98, 2.5, 0.80, C_GATE,
    "collect_articles()\n수집 완료", fs=8.5, bc="#CA8A04", lw=1.2)
arr(ax, 3.0, 7.38, 3.8, 7.38, color=PURPLE, lw=1.6)

# 세션 스토어 박스
ax.add_patch(FancyBboxPatch((3.8, 6.35), 2.8, 1.75,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor=C_SES, edgecolor=PURPLE, linewidth=1.5, zorder=3))
ax.text(5.2, 7.88, '_session["articles"]', ha="center",
        fontsize=8.5, fontweight="bold", color=PURPLE)
ax.text(5.2, 7.48, "article_id → {", ha="center", fontsize=8.0,
        color=C_TXT)
ax.text(5.2, 7.13, '  text: "원문"  ← 격리',
        ha="center", fontsize=7.8, color=RED)
ax.text(5.2, 6.78, '  preview: 앞 300자  ← 공개',
        ha="center", fontsize=7.8, color=GREEN)

# 세션 → Claude (preview만)
arr(ax, 6.6, 7.62, 7.4, 7.62, color=GREEN, lw=1.6)
box(ax, 7.4, 7.10, 2.1, 1.0, C_CLAUDE,
    "Claude Haiku\n에이전트", fs=9.0, bc=BLUE, lw=1.5)
ax.text(8.45, 6.95, "preview만 수신\n(~300 tokens)", ha="center",
        fontsize=7.5, color=GREEN)

ax.text(7.0, 7.98, "preview only\n(300 tokens)", ha="center",
        fontsize=8.0, color=GREEN, fontstyle="italic")

# 세션 → GPT (원문 전달)
arr(ax, 5.2, 6.35, 5.2, 5.72, color=C_SUB, lw=1.3, ls="dashed")
ax.text(5.4, 6.00, "원문 전달 (요약/퀴즈 생성 시)", ha="left",
        fontsize=7.5, color=C_SUB, fontstyle="italic")

# ── 비교 표 ────────────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 3.60), 9.4, 2.30,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.0, zorder=2))
ax.text(0.6, 5.68, "토큰 비용 비교 (토픽 5개, 아티클 3개/토픽 기준)",
        fontsize=9.0, fontweight="bold", color=C_TXT)

headers = ["방식", "Claude 입력 토큰", "비용 절감"]
cols = [1.3, 4.7, 8.0]
for c, h in zip(cols, headers):
    ax.text(c, 5.28, h, ha="center", fontsize=9.0, fontweight="bold", color=C_TXT)
ax.axhline(y=5.10, xmin=0.05, xmax=0.95, color="#CBD5E1", lw=0.8)

rows = [
    ("원문 직접 전달",    "~45,000 tokens", "—",     RED),
    ("세션 스토어 격리",  "~4,500 tokens",  "~90%↓", GREEN),
]
for i, (method, tokens, saving, color) in enumerate(rows):
    y = 4.72 - i * 0.45
    ax.text(cols[0], y, method,  ha="center", fontsize=9.0, color=color)
    ax.text(cols[1], y, tokens,  ha="center", fontsize=9.0, color=color, fontweight="bold")
    ax.text(cols[2], y, saving,  ha="center", fontsize=9.5, color=color, fontweight="bold")

ax.text(0.6, 3.75,
        "* 원문은 GPT-5 생성 시에만 전달 (Claude는 preview 300자만 사용)",
        fontsize=7.8, color=C_SUB, fontstyle="italic")


# ═══════════════════════════════════════════════════════════════
# Figure C — 3단계 품질 파이프라인
# ═══════════════════════════════════════════════════════════════
ax = axes[2]

section_title(ax, 0.3, 11.6,
              "(C)", "3단계 품질 게이트",
              "단계별 탈락으로 저품질 콘텐츠 차단")

# ── 품질 게이트 세로 흐름 ──────────────────────────────────────
stages = [
    (9.8,  "수집 필터",    "신뢰도 점수 + 길이 필터",
     "trust_score",    "≥ 0.65",    C_GATE,  "저품질 제외"),
    (7.6,  "faithfulness 검증",  "GPT-5 요약 → Claude 교차 검증",
     "faithfulness",   "≥ 0.70",    C_GATE,  "policy_rejected"),
    (5.4,  "퀴즈 검증",   "GPT-5 생성 → Claude 교차 검증",
     "verified_count", "> 0",       C_GATE,  "policy_rejected"),
]

ARROW_X = 4.8
DB_X    = 7.5

for (yt, label, sub, gate_key, threshold, gc, fail_lbl) in stages:
    box(ax, 0.4, yt+0.4, 3.8, 0.92, gc, label, sub=sub,
        fs=9.5, bc="#CA8A04", lw=1.5)
    badge(ax, ARROW_X, yt+1.02, f"{gate_key} {threshold}", "#CA8A04", fs=7.5)
    arr(ax, ARROW_X, yt+0.4, ARROW_X, yt-0.32, color=GREEN, lw=1.9)
    badge(ax, ARROW_X, yt+0.10, "PASS", GREEN, fs=7.5)
    arr(ax, 4.2, yt+0.86, DB_X, yt+0.86, color=RED, lw=1.4, rad=-0.2)
    ax.text(DB_X+0.08, yt+0.86, f"✕ {fail_lbl}", ha="left", va="center",
            fontsize=8.0, color=RED)

# 최종 저장
box(ax, 0.4, 3.75, 3.8, 0.80, C_PASS, "Supabase 저장",
    sub="검증된 콘텐츠 + 퀴즈", fs=9.5, bc=GREEN, lw=1.8)
arr(ax, ARROW_X, 5.4, ARROW_X, 4.55, color=GREEN, lw=1.9)
badge(ax, ARROW_X, 4.92, "저장", GREEN, fs=7.5)

# ── 실측 데이터 카드 (바 차트 대체) ────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 2.05), 9.2, 1.48,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.0, zorder=2))
ax.text(0.6, 3.32, "단계별 탈락 수치 (실측)", fontsize=9.0,
        fontweight="bold", color=C_TXT)

# 숫자 카드 3개
card_data = [
    ("수집 필터",   "다수 제외",  "#CA8A04", "quality_rejected\ntrust < 0.65"),
    ("faithfulness 검증", "일부 탈락",  RED,       "policy_rejected\nfaithfulness < 0.70"),
    ("퀴즈 검증",  "106 / 147\n탈락 72%",  ORANGE,    "policy_rejected\nverified = 0"),
]
card_x = [0.5, 3.6, 6.7]
for i, (title, val, color, ft) in enumerate(card_data):
    cx = card_x[i]
    ax.add_patch(FancyBboxPatch((cx, 2.12), 2.85, 1.08,
        boxstyle="round,pad=0,rounding_size=0.2",
        facecolor="white", edgecolor=color, linewidth=1.5, zorder=3))
    ax.text(cx+1.42, 2.94, title, ha="center", fontsize=8.0,
            color=C_TXT, fontweight="bold")
    ax.text(cx+1.42, 2.60, val, ha="center", fontsize=8.5,
            color=color, fontweight="bold", linespacing=1.3)
    ax.text(cx+1.42, 2.22, ft, ha="center", fontsize=6.8,
            color=C_SUB, linespacing=1.3)

# ── 설계 근거 ──────────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((0.3, 0.30), 9.2, 1.60,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor="#F0FDF4", edgecolor=GREEN, linewidth=1.2,
    linestyle="--", zorder=2))
ax.text(0.6, 1.68, "설계 근거", fontsize=9.0, fontweight="bold", color=GREEN)
ax.text(0.6, 1.30,
        "• 불확실한 콘텐츠를 유저에게 노출하는 것이 가장 큰 리스크",
        fontsize=8.5, color=C_TXT)
ax.text(0.6, 0.94,
        "• 탈락 유형 분류로 '왜 실패했는지' 사후 추적 가능 (Observability)",
        fontsize=8.5, color=C_TXT)
ax.text(0.6, 0.58,
        "• 이전: 검증 오류 → 통과(보수적) / 현재: 검증 오류 → 탈락(엄격)",
        fontsize=8.5, color=C_TXT)


# ═══════════════════════════════════════════════════════════════
# 전체 제목 + 캡션
# ═══════════════════════════════════════════════════════════════
fig.text(0.5, 0.985,
         "Figure 2. BriefUp 에이전트 핵심 설계 결정",
         ha="center", va="top", fontsize=15, fontweight="bold", color=C_HL)
fig.text(0.5, 0.963,
         "(A) 이중 모델 역할 분리와 교차 검증 루프.  "
         "(B) 세션 스토어를 통한 원문 격리 및 토큰 비용 최적화.  "
         "(C) 3단계 품질 게이트와 실패 유형 분류 체계.",
         ha="center", va="top", fontsize=9.5, color=C_SUB)

# 서브플롯 간 구분선
for x in [0.375, 0.675]:
    fig.add_artist(plt.matplotlib.lines.Line2D(
        [x, x], [0.03, 0.96], transform=fig.transFigure,
        color="#E2E8F0", linewidth=1.5))

# ── 저장 ────────────────────────────────────────────────────────
out = os.path.dirname(os.path.abspath(__file__))
plt.tight_layout(rect=[0, 0.01, 1, 0.96], pad=1.5)
fig.savefig(f"{out}/design_decisions.svg", format="svg",
            bbox_inches="tight", facecolor="white")
fig.savefig(f"{out}/design_decisions.png", format="png",
            dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("저장 완료: design_decisions.svg / design_decisions.png")
