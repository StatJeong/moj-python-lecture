"""3장 '그래프의 구조'에 쓰는 그림을 만든다 (웹 강의자료 전용).

    python tools/make_structure_figs.py

만드는 그림
  images/anatomy_ko.png       그래프 각 부분의 이름 (matplotlib 공식 예제를 한국어로 바꿔 다시 그림)
  images/layers.gif           코드 한 줄마다 그래프에 층이 하나씩 쌓이는 움짤
  images/seaborn_stack.png    표 → seaborn → matplotlib → 화면으로 이어지는 층 구조
  images/seaborn_functions.png seaborn 함수 구성

anatomy_ko.png는 matplotlib 공식 갤러리의 "Anatomy of a figure" 예제
(https://matplotlib.org/stable/gallery/showcase/anatomy.html) 코드를 바탕으로,
설명 글을 한국어로 바꾸고 일부 항목을 줄였다. Matplotlib 라이선스(PSF 기반)에 따라
원 저작권 표시: Copyright (c) 2012- Matplotlib Development Team; All Rights Reserved.
"""

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.patheffects import withStroke  # noqa: E402
from matplotlib.ticker import AutoMinorLocator, MultipleLocator  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from code_stepper import CODE_FONT, TEXT_FONT, C  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
NANUM = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
if Path(NANUM).exists():
    fm.fontManager.addfont(NANUM)
    BODY = "NanumGothic"
else:
    BODY = TEXT_FONT
plt.rcParams["font.family"] = BODY
plt.rcParams["axes.unicode_minus"] = False


# ------------------------------------------------------------------ 1. 그래프의 각 부분
def anatomy():
    royal_blue = [0, 20 / 256, 82 / 256]
    np.random.seed(19680801)
    X = np.linspace(0.5, 3.5, 100)
    Y1 = 3 + np.cos(X)
    Y2 = 1 + np.cos(1 + X / 0.75) / 2
    Y3 = np.random.uniform(Y1, Y2, len(X))

    fig = plt.figure(figsize=(7.5, 7.5))
    ax = fig.add_axes((0.2, 0.17, 0.68, 0.7), aspect=1)
    ax.xaxis.set_major_locator(MultipleLocator(1.000))
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.yaxis.set_major_locator(MultipleLocator(1.000))
    ax.yaxis.set_minor_locator(AutoMinorLocator(4))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    ax.tick_params(which="major", width=1.0, length=10, labelsize=14)
    ax.tick_params(which="minor", width=1.0, length=5)
    ax.grid(linestyle="--", linewidth=0.5, color=".25", zorder=-10)
    ax.plot(X, Y1, c="C0", lw=2.5, label="파란 선", zorder=10)
    ax.plot(X, Y2, c="C1", lw=2.5, label="주황 선")
    ax.plot(X[::3], Y3[::3], linewidth=0, markersize=9, marker="s",
            markerfacecolor="none", markeredgecolor="C4", markeredgewidth=2.5)
    ax.set_title("그래프의 구조", fontsize=20, verticalalignment="bottom")
    ax.set_xlabel("x축 이름", fontsize=14)
    ax.set_ylabel("y축 이름", fontsize=14)
    ax.legend(loc="upper right", fontsize=14)

    def annotate(x, y, text, code):
        c = Circle((x, y), radius=0.15, clip_on=False, zorder=10, linewidth=2.5,
                   edgecolor=royal_blue + [0.6], facecolor="none",
                   path_effects=[withStroke(linewidth=7, foreground="white")])
        ax.add_artist(c)
        for path_effects in [[withStroke(linewidth=7, foreground="white")], []]:
            color = "white" if path_effects else royal_blue
            ax.text(x, y - 0.2, text, zorder=100, ha="center", va="top", color=color,
                    fontsize=12, fontfamily=BODY, path_effects=path_effects)
            color = "white" if path_effects else "black"
            ax.text(x, y - 0.36, code, zorder=100, ha="center", va="top", color=color,
                    fontfamily="DejaVu Sans Mono", fontsize=9.5, path_effects=path_effects)

    annotate(-0.03, 1.0, "눈금", "ax.set_yticks")
    annotate(-0.15, 3.00, "눈금 숫자", "ax.set_yticks")
    annotate(1.68, -0.39, "x축 이름", "ax.set_xlabel")
    annotate(-0.38, 1.67, "y축 이름", "ax.set_ylabel")
    annotate(1.52, 4.15, "제목", "ax.set_title")
    annotate(1.75, 2.80, "선", "ax.plot")
    annotate(2.25, 1.54, "점", "ax.scatter")
    annotate(3.00, 3.00, "눈금선", "ax.grid")
    annotate(3.60, 3.58, "범례", "ax.legend")
    annotate(2.5, 0.55, "그래프 칸 (Axes)", "plt.subplots")
    annotate(4, 4.5, "그림판 (Figure)", "plt.figure")
    annotate(0.65, 0.01, "x축", "ax.xaxis")
    annotate(0, 0.36, "y축", "ax.yaxis")
    annotate(4.0, 0.7, "테두리", "ax.spines")
    fig.patch.set(linewidth=4, edgecolor="0.5")
    fig.text(0.5, 0.015, "matplotlib 공식 예제 'Anatomy of a figure'를 바탕으로 한국어로 다시 그림",
             ha="center", fontsize=9, color="0.4")
    fig.savefig(IMG / "anatomy_ko.png", dpi=110)
    plt.close(fig)


# ------------------------------------------------------------------ 2. 층이 쌓이는 움짤
LAYER_CODE = [
    ('plt.figure(figsize=(6, 4))', "빈 그림판을 만듭니다"),
    ('plt.bar(죄명별.index, 죄명별.values)', "막대 층을 올립니다 (그래프 칸과 축도 함께 생김)"),
    ('plt.axhline(죄명별.mean(), color="gray", linestyle="--")', "평균선 층을 올립니다"),
    ('plt.title("죄명별 수용자 수")', "제목을 붙입니다"),
    ('plt.xlabel("죄명")', "x축 이름을 붙입니다"),
    ('plt.ylabel("인원(명)")', "y축 이름을 붙입니다"),
    ('plt.show()', "다 쌓은 그림을 화면에 보여줍니다"),
]


def _chart_image(n_lines, 죄명별):
    """앞에서부터 n_lines 줄까지 실제로 실행한 그림을 이미지로 돌려준다."""
    plt.close("all")
    ns = {"plt": plt, "죄명별": 죄명별}
    for code, _ in LAYER_CODE[:n_lines]:
        if code.startswith("plt.show"):
            continue
        exec(code, ns)
    fig = plt.gcf()
    fig.patch.set(linewidth=2, edgecolor="0.6")     # 그림판 테두리를 보이게
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, facecolor="white", edgecolor=fig.get_edgecolor())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def layers_gif():
    수용자 = pd.read_csv(ROOT / "data" / "inmates.csv")
    죄명별 = 수용자["죄명"].value_counts()
    frames = []
    for k in range(1, len(LAYER_CODE) + 1):
        chart = _chart_image(k, 죄명별)
        fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(0.03, 0.945, "그래프는 한 줄씩 층을 쌓아 그립니다", family=TEXT_FONT, size=21,
                weight="bold", color=C["text"], va="center")
        ax.text(0.97, 0.945, f"{k} / {len(LAYER_CODE)}", family=TEXT_FONT, size=14, color=C["sub"],
                va="center", ha="right")
        ax.add_patch(FancyBboxPatch((0.03, 0.17), 0.94, 0.71, boxstyle="round,pad=0,rounding_size=0.008",
                                    fc=C["panel"], ec=C["border"], lw=1.2))
        ax.text(0.045, 0.865, "코드 (노란 줄 = 방금 실행한 줄)", family=TEXT_FONT, size=12, color=C["sub"], va="top")
        lh = 0.075
        for i, (code, _) in enumerate(LAYER_CODE, start=1):
            y = 0.79 - (i - 1) * lh
            if i == k:
                ax.add_patch(Rectangle((0.034, y - lh / 2), 0.43, lh, fc=C["line_hl"], ec="none"))
                ax.plot([0.042], [y], marker=">", ms=10, color=C["mark"])
            done = i <= k
            ax.text(0.068, y, str(i), family=CODE_FONT, size=12, color=C["sub"], va="center", ha="right")
            short = code if len(code) <= 40 else code[:38] + "…"
            ax.text(0.08, y, short, family=CODE_FONT, size=12.5, va="center",
                    color=C["text"] if done else "#B0B6BF")
        ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.11, boxstyle="round,pad=0,rounding_size=0.008",
                                    fc=C["cap_bg"], ec="none"))
        ax.text(0.05, 0.085, f"{k}번 줄: {LAYER_CODE[k - 1][1]}", family=TEXT_FONT, size=16,
                color=C["text"], va="center")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, facecolor="white")
        plt.close(fig)
        buf.seek(0)
        frame = Image.open(buf).convert("RGB")
        # 오른쪽 칸에 실제 그림을 붙인다
        box_w, box_h = int(1280 * 0.47), int(720 * 0.62)
        chart.thumbnail((box_w, box_h))
        frame.paste(chart, (int(1280 * 0.49) + (box_w - chart.width) // 2,
                            int(720 * 0.17) + (int(720 * 0.66) - chart.height) // 2))
        frames.append(frame)
    durations = [2200] * (len(frames) - 1) + [4500]
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(IMG / "layers.gif", save_all=True, append_images=pal[1:], duration=durations, loop=0)
    chk = ROOT.parent / "checks"
    if chk.exists():
        for i in (0, 1, 2, 5):
            frames[i].save(chk / f"layers_{i}.png")


# ------------------------------------------------------------------ 3. seaborn과 matplotlib의 층
def seaborn_stack():
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    층 = [
        ("화면 / 그림 파일", "plt.show(), plt.savefig()", "#EEF2F7"),
        ("matplotlib", "그림판, 그래프 칸, 막대·선·점, 제목, 축, 범례를 실제로 그림", "#DCE8F7"),
        ("seaborn", "표를 받아 개수·평균·회귀선을 계산하고, 색 구분과 범례를 정해 matplotlib에 맡김", "#DCEFDD"),
        ("pandas 표 (DataFrame)", "수용자 데이터: 열 이름으로 x, y, hue를 지정", "#FFF3D6"),
    ]
    for i, (이름, 설명, 색) in enumerate(층):
        y = 4.3 - i * 1.25
        ax.add_patch(FancyBboxPatch((0.4, y), 9.2, 0.95, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=색, ec="0.55", lw=1.2))
        ax.text(0.75, y + 0.62, 이름, fontsize=15, va="center")
        ax.text(0.75, y + 0.27, 설명, fontsize=11, va="center", color="0.3")
        if i < len(층) - 1:
            ax.annotate("", xy=(5, y + 0.02), xytext=(5, y - 0.28),
                        arrowprops=dict(arrowstyle="->", color="0.4", lw=1.5))
    ax.text(9.6, 0.05, "아래층이 위층에 재료를 넘겨줍니다", ha="right", fontsize=10, color="0.45")
    fig.savefig(IMG / "seaborn_stack.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------------ 4. seaborn 함수 구성
def seaborn_functions():
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    묶음 = [
        ("관계 (relational)", "relplot", ["scatterplot", "lineplot"], "#DCE8F7", "두 숫자 사이의 관계"),
        ("분포 (distributions)", "displot", ["histplot", "kdeplot", "ecdfplot", "rugplot"], "#DCEFDD",
         "숫자 하나가 어떻게 퍼져 있는지"),
        ("범주 (categorical)", "catplot", ["stripplot", "swarmplot", "boxplot", "violinplot",
                                          "pointplot", "barplot", "countplot"], "#FFF3D6", "그룹별 비교"),
    ]
    쓴것 = {}   # 이 강의에서 쓰는 seaborn 함수는 묶음 밖의 heatmap 하나
    for j, (이름, 큰함수, 함수들, 색, 뜻) in enumerate(묶음):
        x0 = 0.3 + j * 3.6
        ax.add_patch(FancyBboxPatch((x0, 0.35), 3.3, 4.95, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=색, ec="0.55", lw=1.2))
        ax.text(x0 + 1.65, 5.0, 이름, ha="center", fontsize=14)
        ax.text(x0 + 1.65, 4.62, 뜻, ha="center", fontsize=10, color="0.35")
        ax.text(x0 + 1.65, 4.12, 큰함수, ha="center", fontsize=13, family="DejaVu Sans Mono",
                bbox=dict(boxstyle="round", fc="white", ec="0.5"))
        for i, f in enumerate(함수들):
            ax.text(x0 + 1.65, 3.45 - i * 0.43, f + (f"  ({쓴것[f]})" if f in 쓴것 else ""), ha="center",
                    fontsize=11.5, family="DejaVu Sans Mono" if f not in 쓴것 else BODY,
                    color="black" if f in 쓴것 else "0.3")
    ax.text(5.5, 0.05, "위쪽 큰 함수(relplot 등)는 그림판 전체를, 아래 함수들은 그래프 칸 하나를 그립니다. "
            "이 강의에서 쓰는 heatmap(히트맵)은 이 묶음 밖의 함수입니다(3장 3.7절, 6장 6.7절).",
            ha="center", fontsize=9.5, color="0.35")
    fig.savefig(IMG / "seaborn_functions.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    anatomy()
    layers_gif()
    seaborn_stack()
    seaborn_functions()
    print("done")
