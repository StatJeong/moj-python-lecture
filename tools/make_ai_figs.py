"""5장(AI와 함께 분석하기)의 흐름 그림을 만든다. 사이트에만 싣고 Colab 노트북에는 넣지 않는다.

    python tools/make_ai_figs.py

만드는 그림: images/ai/flow.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images" / "ai"
OUT.mkdir(parents=True, exist_ok=True)

for 파일 in ("NanumGothic.ttf", "NanumGothicBold.ttf"):
    fm.fontManager.addfont(f"/usr/share/fonts/truetype/nanum/{파일}")
plt.rcParams["font.family"] = "NanumGothic"

진회색, 회색, 파랑, 주황, 빨강, 초록 = "#3C4043", "#9AA0A6", "#3B6FB6", "#D9822B", "#D0453A", "#2E8B57"


def 상자(ax, x, y, w, h, 제목, 내용, 테두리, 바탕):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                linewidth=2, edgecolor=테두리, facecolor=바탕))
    ax.text(x + 0.03, y + h - 0.06, 제목, fontsize=15, fontweight="bold", color=테두리, va="top")
    ax.text(x + 0.03, y + h - 0.17, 내용, fontsize=11.5, color=진회색, va="top", linespacing=1.7)


def 화살표(ax, 시작, 끝, 글, 색, 글위치, 굽음=0.0):
    ax.add_patch(FancyArrowPatch(시작, 끝, arrowstyle="-|>", mutation_scale=22, linewidth=2.2,
                                 color=색, connectionstyle=f"arc3,rad={굽음}"))
    ax.text(*글위치, 글, fontsize=11.5, color=색, ha="center", va="center", linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none"))


fig, ax = plt.subplots(figsize=(12, 5.6))
ax.set_xlim(0, 1.6)
ax.set_ylim(0, 1)
ax.axis("off")

상자(ax, 0.03, 0.12, 0.52, 0.78, "내 자리 (Colab, 기관 내부)",
     "수용자 표 (대외비)\n· 실제 값은 여기에만 있음\n\n받은 코드를 붙여 넣어 실행\n결과 표와 그래프를 내가 확인\n\n결과는 초안, 판단과 보고는 내가", 파랑, "#EEF3FA")
상자(ax, 1.05, 0.12, 0.52, 0.78, "Claude (외부 서비스)",
     "실제 값을 모름\n· 변수 이름과 형식만 앎\n\n코드를 써 주고\n코드와 결과의 뜻을 설명함\n\n같은 질문에도 답이\n조금씩 달라질 수 있음", 주황, "#FDF3E8")

화살표(ax, (0.57, 0.74), (1.03, 0.74), "① 변수 설명서 + 하고 싶은 것", 진회색, (0.80, 0.80))
화살표(ax, (1.03, 0.52), (0.57, 0.52), "② 코드", 진회색, (0.80, 0.58))
화살표(ax, (0.57, 0.30), (1.03, 0.30), "③ 결과를 보고 다시 질문\n(오류 메시지, 궁금한 코드 줄)", 진회색, (0.80, 0.22))

ax.text(0.80, 0.97, "파일과 사람별 실제 값은 보내지 않음", fontsize=13, color=빨강, ha="center",
        fontweight="bold")
저장 = OUT / "flow.png"
fig.savefig(저장, dpi=150, bbox_inches="tight", facecolor="white")
print("저장:", 저장)
