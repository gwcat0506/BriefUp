"""
발표용 이미지 생성 — 실제 DB 데이터 기반
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT = "/Users/gwcat/Desktop/BrefUp/docs/presentation"
DARK_BG   = "#0f1117"
CARD_BG   = "#1a1d27"
ACCENT    = "#6c63ff"
GREEN     = "#22c55e"
RED       = "#ef4444"
YELLOW    = "#f59e0b"
GRAY      = "#6b7280"
WHITE     = "#f1f5f9"
SUBTEXT   = "#94a3b8"

plt.rcParams.update({
    "font.family": "AppleGothic",   # 한글 폰트
    "text.color":  WHITE,
    "axes.facecolor": DARK_BG,
    "figure.facecolor": DARK_BG,
})

# ─────────────────────────────────────────────
# 이미지 1: Run 이력 테이블
# ─────────────────────────────────────────────
def img1_run_history():
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis("off")
    fig.patch.set_facecolor(DARK_BG)

    # 제목
    fig.text(0.5, 0.93, "Pipeline Run 이력", ha="center", fontsize=22,
             fontweight="bold", color=WHITE)
    fig.text(0.5, 0.87, "매일 자동 실행 — 모든 실행이 기록됩니다",
             ha="center", fontsize=13, color=SUBTEXT)

    cols = ["실행 시각 (KST)", "소요 시간", "토픽", "수집", "저장", "퀴즈", "비용"]
    rows = [
        ["06-08  17:21", "3분 07초", "9개", "87건", "26개", "41개", "$0.23"],
        ["06-08  17:12", "1분 33초", "9개", "39건", "10개", "15개", "$0.10"],
        ["06-07  03:23", "53초",    "2개",  "5건",   "3개",  "5개",  "$0.04"],
        ["06-07  18:14", "2분 33초", "9개", "—",    "10개", "15개",  "—"],
    ]

    col_w = [0.22, 0.13, 0.09, 0.09, 0.09, 0.09, 0.10]
    xs = [0.04]
    for w in col_w[:-1]:
        xs.append(xs[-1] + w)

    # 헤더
    header_y = 0.76
    for i, (c, x) in enumerate(zip(cols, xs)):
        ax.text(x, header_y, c, transform=fig.transFigure,
                fontsize=11, color=ACCENT, fontweight="bold")

    line = plt.Line2D([0.03, 0.97], [header_y - 0.04, header_y - 0.04],
                      transform=fig.transFigure, color=ACCENT, linewidth=0.8)
    fig.add_artist(line)

    row_colors = [GREEN, WHITE, WHITE, WHITE]
    row_ys = [0.66, 0.53, 0.40, 0.27]

    for ri, (row, ry, rc) in enumerate(zip(rows, row_ys, row_colors)):
        # 첫 행 강조 박스
        if ri == 0:
            rect = FancyBboxPatch((0.03, ry - 0.05), 0.94, 0.14,
                                  transform=fig.transFigure,
                                  boxstyle="round,pad=0.01",
                                  facecolor="#1e2235", edgecolor=ACCENT,
                                  linewidth=1.2, zorder=0)
            fig.add_artist(rect)

        for val, x in zip(row, xs):
            color = GREEN if ri == 0 else WHITE
            ax.text(x, ry, val, transform=fig.transFigure,
                    fontsize=12, color=color,
                    fontweight="bold" if ri == 0 else "normal")

    # 최신 run 강조 라벨
    ax.text(0.97, 0.66, "← 최신", transform=fig.transFigure,
            fontsize=10, color=GREEN, ha="right", style="italic")

    # 하단 설명
    fig.text(0.5, 0.10,
             "pipeline_runs 테이블  |  Supabase에 실시간 기록",
             ha="center", fontsize=10, color=GRAY)

    plt.tight_layout()
    plt.savefig(f"{OUT}/01_run_history.png", dpi=160, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.close()
    print("✓ 01_run_history.png")


# ─────────────────────────────────────────────
# 이미지 2: 133 스텝 Tool Call 타임라인
# ─────────────────────────────────────────────
def img2_tool_timeline():
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    fig.text(0.5, 0.95, "133 스텝 Tool Call 로그 (1회 실행)", ha="center",
             fontsize=20, fontweight="bold", color=WHITE)
    fig.text(0.5, 0.90, "Claude가 어떤 순서로 무엇을 호출했는지 — 전부 기록됩니다",
             ha="center", fontsize=12, color=SUBTEXT)

    # 실제 데이터
    tools = {
        "collect":   {"steps": list(range(1, 10)),   "color": "#3b82f6", "label": "collect (기사 수집)"},
        "summarize": {"steps": list(range(10, 59)),  "color": "#8b5cf6", "label": "summarize (요약)"},
        "quiz_gen":  {"steps": list(range(59, 108)), "color": YELLOW,    "label": "quiz_gen (퀴즈 생성+검증)"},
        "save":      {"steps": list(range(108, 134)),"color": GREEN,     "label": "save (DB 저장)"},
    }

    tool_order = ["collect", "summarize", "quiz_gen", "save"]
    y_positions = {"collect": 3, "summarize": 2, "quiz_gen": 1, "save": 0}
    y_labels    = ["save", "quiz_gen", "summarize", "collect"]

    ax.set_xlim(0, 135)
    ax.set_ylim(-0.7, 3.7)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(y_labels, fontsize=12, color=WHITE)
    ax.set_xlabel("step_order", fontsize=11, color=SUBTEXT)
    ax.tick_params(colors=SUBTEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3148")

    ax.grid(axis="x", color="#2d3148", linewidth=0.5, linestyle="--")

    for name, info in tools.items():
        y = y_positions[name]
        for s in info["steps"]:
            ax.bar(s, 0.6, bottom=y - 0.3, width=0.85,
                   color=info["color"], alpha=0.85, zorder=2)

    # 단계 구분선 + 라벨
    boundaries = [(1, 9, "Step 1–9\ncollect"), (10, 58, "Step 10–58\nsummarize"),
                  (59, 107, "Step 59–107\nquiz_gen"), (108, 133, "Step 108–133\nsave")]
    for start, end, label in boundaries:
        mid = (start + end) / 2
        ax.axvline(x=start - 0.5, color="#2d3148", linewidth=1.2, linestyle=":")

    # 특별 강조: quiz_gen verified=0 사례
    for s in [59, 60, 62, 67, 70, 72, 79, 80, 83, 85, 88, 92, 93, 94, 96, 98, 100, 103]:
        ax.bar(s, 0.6, bottom=y_positions["quiz_gen"] - 0.3, width=0.85,
               color=RED, alpha=0.9, zorder=3)

    # 범례
    legend_items = [
        mpatches.Patch(color="#3b82f6", label="collect"),
        mpatches.Patch(color="#8b5cf6", label="summarize"),
        mpatches.Patch(color=YELLOW,   label="quiz_gen (통과)"),
        mpatches.Patch(color=RED,      label="quiz_gen (전량 탈락)"),
        mpatches.Patch(color=GREEN,    label="save"),
    ]
    ax.legend(handles=legend_items, loc="upper right", fontsize=10,
              facecolor=CARD_BG, edgecolor=ACCENT, labelcolor=WHITE)

    ax.text(0.5, -0.55,
            "pipeline_logs 테이블  |  tool_name / step_order / duration_ms / status 기록",
            transform=ax.transAxes, ha="center", fontsize=9, color=GRAY)

    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(f"{OUT}/02_tool_timeline.png", dpi=160, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.close()
    print("✓ 02_tool_timeline.png")


# ─────────────────────────────────────────────
# 이미지 3: 퀴즈 검증 (Self-Verify 증거)
# ─────────────────────────────────────────────
def img3_quiz_verify():
    fig = plt.figure(figsize=(14, 7))
    fig.patch.set_facecolor(DARK_BG)

    fig.text(0.5, 0.95, "Self-Verify: 검증기가 실제로 탈락시킵니다",
             ha="center", fontsize=20, fontweight="bold", color=WHITE)
    fig.text(0.5, 0.90,
             "generated=3 이 항상 saved=3 이 아닙니다",
             ha="center", fontsize=12, color=SUBTEXT)

    # 왼쪽: 전체 파이 차트
    ax1 = fig.add_axes([0.05, 0.12, 0.35, 0.68])
    ax1.set_facecolor(DARK_BG)

    generated = 147
    verified  = 41
    rejected  = generated - verified

    wedges, texts, autotexts = ax1.pie(
        [verified, rejected],
        labels=["검증 통과\n41개", "탈락\n106개"],
        colors=[GREEN, RED],
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.65,
        textprops={"color": WHITE, "fontsize": 13},
        wedgeprops={"linewidth": 2, "edgecolor": DARK_BG},
    )
    for at in autotexts:
        at.set_fontsize(14)
        at.set_fontweight("bold")

    ax1.set_title(f"퀴즈 생성 시도 {generated}개\n(49 아티클 × 3문제)",
                  color=WHITE, fontsize=12, pad=12)

    # 오른쪽: 개별 케이스 바 차트 (대표 20개)
    ax2 = fig.add_axes([0.47, 0.12, 0.50, 0.68])
    ax2.set_facecolor(DARK_BG)

    # 실제 quiz_gen verified 값 (step 59~107 중 대표 20개)
    sample_steps = [59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78]
    sample_verified = [0, 0, 2, 0, 1, 1, 2, 2, 0, 2, 1, 0, 1, 0, 3, 1, 2, 1, 1, 3]
    sample_categories = [
        "AI/ML","건강","AI/ML","건강","AI/ML","AI/ML","철학","철학",
        "과기","과기","과기","기타","AI/ML","철학","건강","인문",
        "건강","AI/ML","AI/ML","건강"
    ]
    colors_bar = [GREEN if v > 0 else RED for v in sample_verified]

    bars = ax2.bar(range(len(sample_steps)), sample_verified,
                   color=colors_bar, alpha=0.85, width=0.7, zorder=2)

    # generated=3 기준선
    ax2.axhline(y=3, color=SUBTEXT, linewidth=1.2, linestyle="--", alpha=0.6)
    ax2.text(19.6, 3.05, "생성 시도\n(3개)", color=SUBTEXT, fontsize=9, ha="right")

    ax2.set_xticks(range(len(sample_steps)))
    ax2.set_xticklabels([f"#{s}" for s in sample_steps],
                        fontsize=8, rotation=45, color=SUBTEXT)
    ax2.set_yticks([0, 1, 2, 3])
    ax2.set_yticklabels(["0", "1", "2", "3 ✓"], color=WHITE, fontsize=11)
    ax2.set_ylabel("검증 통과 퀴즈 수", color=SUBTEXT, fontsize=11)
    ax2.set_title("step별 verified 수 (59~78번 스텝)", color=WHITE, fontsize=12)
    ax2.tick_params(colors=SUBTEXT)
    for spine in ax2.spines.values():
        spine.set_edgecolor("#2d3148")
    ax2.grid(axis="y", color="#2d3148", linewidth=0.5, linestyle="--")

    # 0개 탈락 라벨
    for i, v in enumerate(sample_verified):
        if v == 0:
            ax2.text(i, 0.12, "전량\n탈락", ha="center", fontsize=7,
                     color=RED, fontweight="bold")

    # 하단 설명
    fig.text(0.5, 0.04,
             '"불확실하면 통과"가 아닌  "불확실하면 탈락"  —  verifier.py',
             ha="center", fontsize=11, color=ACCENT, style="italic")

    plt.savefig(f"{OUT}/03_quiz_verify.png", dpi=160, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.close()
    print("✓ 03_quiz_verify.png")


# ─────────────────────────────────────────────
# 이미지 4: 비용 추적
# ─────────────────────────────────────────────
def img4_cost():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.patch.set_facecolor(DARK_BG)
    for ax in axes:
        ax.set_facecolor(DARK_BG)

    fig.text(0.5, 0.96, "비용 추적 — 실행별 Claude + GPT 토큰 집계",
             ha="center", fontsize=18, fontweight="bold", color=WHITE)

    # 왼쪽: 최신 run 토큰 비율
    ax = axes[0]
    labels  = ["Claude\nHaiku", "GPT-4o\nmini"]
    input_t = [91816,  266341]
    output_t= [14433,   47730]
    x = np.array([0, 1])
    w = 0.35

    b1 = ax.bar(x - w/2, input_t,  w, label="input tokens",  color=ACCENT,  alpha=0.85)
    b2 = ax.bar(x + w/2, output_t, w, label="output tokens", color="#a78bfa", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=13, color=WHITE)
    ax.set_ylabel("tokens", color=SUBTEXT, fontsize=11)
    ax.set_title("토큰 사용량 (최신 실행)", color=WHITE, fontsize=13)
    ax.tick_params(colors=SUBTEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3148")
    ax.legend(facecolor=CARD_BG, edgecolor=ACCENT, labelcolor=WHITE, fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}K"))
    ax.grid(axis="y", color="#2d3148", linewidth=0.5, linestyle="--")

    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 2000,
                f"{int(h/1000)}K", ha="center", fontsize=9, color=SUBTEXT)

    # 오른쪽: run별 비용
    ax2 = axes[1]
    run_labels = ["06-07\n#4", "06-07\n#3", "06-08\n#2", "06-08\n#1"]
    costs      = [0.0,        0.042,        0.098,         0.232]
    colors_c   = [GRAY, "#3b82f6", "#8b5cf6", GREEN]

    bars = ax2.barh(run_labels, costs, color=colors_c, alpha=0.85, height=0.5)
    ax2.set_xlabel("비용 (USD)", color=SUBTEXT, fontsize=11)
    ax2.set_title("실행별 비용", color=WHITE, fontsize=13)
    ax2.tick_params(colors=WHITE)
    for spine in ax2.spines.values():
        spine.set_edgecolor("#2d3148")
    ax2.grid(axis="x", color="#2d3148", linewidth=0.5, linestyle="--")

    for bar, cost in zip(bars, costs):
        if cost > 0:
            ax2.text(cost + 0.002, bar.get_y() + bar.get_height()/2,
                     f"${cost:.3f}", va="center", fontsize=11,
                     color=WHITE, fontweight="bold")
        else:
            ax2.text(0.003, bar.get_y() + bar.get_height()/2,
                     "기록 없음", va="center", fontsize=10, color=GRAY)

    # 하단 설명
    fig.text(0.5, 0.02,
             "pipeline_runs.stats  |  claude_input / openai_input / cost_usd 집계",
             ha="center", fontsize=10, color=GRAY)

    plt.tight_layout(rect=[0, 0.05, 1, 0.94])
    plt.savefig(f"{OUT}/04_cost_tracking.png", dpi=160, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.close()
    print("✓ 04_cost_tracking.png")


if __name__ == "__main__":
    img1_run_history()
    img2_tool_timeline()
    img3_quiz_verify()
    img4_cost()
    print("\n완료! docs/presentation/ 에 이미지 4장 저장됨")
