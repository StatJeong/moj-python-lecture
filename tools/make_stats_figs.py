"""4장(기초통계와 회귀)에 넣는 설명 그림을 만든다. 사이트에만 싣고 Colab 노트북에는 넣지 않는다.

    python tools/make_stats_figs.py

만드는 그림 (images/stats/):
- ttest_null.png       : 귀무가설에서의 t분포, 기각 영역, 실제 t값과 p값
- ols_residuals.png    : 평균선과 회귀직선의 잔차 비교 (최소제곱법, 결정계수)
- logit_vs_linear.png  : 0/1 자료를 직선과 S자 곡선으로 맞춘 비교
- sigmoid.png          : 일차식(로그 오즈)과 시그모이드 함수
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images" / "stats"
OUT.mkdir(parents=True, exist_ok=True)

fm.fontManager.addfont("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
fm.fontManager.addfont("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "dejavusans"

파랑, 빨강, 회색, 진회색, 초록 = "#3B6FB6", "#D0453A", "#9AA0A6", "#4A4F55", "#2E8B57"

자료 = pd.read_csv(ROOT / "data" / "inmates.csv")
자료["징벌여부"] = (자료["징벌횟수"] > 0).astype(int)


def 다듬기(ax):
    ax.spines[["top", "right"]].set_visible(False)


def 저장(fig, 이름):
    fig.savefig(OUT / 이름, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("저장:", OUT / 이름)


# ------------------------------------------------------------------ t검정
def t검정그림():
    참여 = 자료[자료["직업훈련"] == "Y"]["징벌횟수"]
    비참여 = 자료[자료["직업훈련"] == "N"]["징벌횟수"]
    결과 = stats.ttest_ind(참여, 비참여, equal_var=False)
    t값, p값, 자유도 = float(결과.statistic), float(결과.pvalue), float(결과.df)
    임계 = stats.t.ppf(0.975, 자유도)

    x = np.linspace(-5.2, 5.2, 800)
    y = stats.t.pdf(x, 자유도)
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    ax.plot(x, y, color=진회색, lw=2)

    for 쪽 in (x <= -임계, x >= 임계):
        ax.fill_between(x, y, where=쪽, color=빨강, alpha=0.18, lw=0)
    for 쪽 in (x <= -abs(t값), x >= abs(t값)):
        ax.fill_between(x, y, where=쪽, color=빨강, alpha=0.75, lw=0)

    ax.plot([t값, t값], [0, 0.13], color=빨강, lw=2.2)
    ax.plot([-t값, -t값], [0, 0.13], color=빨강, lw=1.2, ls="--")
    for 값 in (-임계, 임계):
        ax.plot([값, 값], [0, 0.3], color=회색, lw=1, ls=":")
        ax.text(값, 0.305, f"{값:+.2f}", ha="center", va="bottom", fontsize=9, color=진회색)

    ax.annotate(f"실제로 나온 t = {t값:.2f}", xy=(t값, 0.13), xytext=(-5.1, 0.24),
                fontsize=11, color=빨강, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=빨강))
    ax.annotate(f"반대쪽 +{abs(t값):.2f} 바깥도\n함께 셈", xy=(abs(t값), 0.13), xytext=(4.1, 0.22),
                fontsize=9.5, color=빨강, ha="center",
                arrowprops=dict(arrowstyle="->", color=빨강, lw=0.8))
    ax.text(0, 0.17, "평균이 같다면\nt값은 대부분\n0 근처에 나옴", ha="center", fontsize=10.5, color=진회색)
    ax.text(-5.1, 0.44, "옅은 빨강: 유의수준 5% 영역 (양쪽 꼬리 2.5%씩)\n진한 빨강: 실제 t값보다 바깥쪽 넓이 = p값",
            ha="left", va="top", fontsize=9.5, color=진회색, linespacing=1.5)

    ax.set_title(f"두 집단 평균이 같다고 가정할 때 t값이 나오는 분포 (t분포, 자유도 {자유도:.1f})",
                 loc="left", fontsize=12.5, pad=12)
    ax.text(0.0, -0.2, f"진한 빨강 넓이 = p값 = {p값:.3f}  →  0.05보다 작으므로 '두 평균이 같다'는 가정을 받아들이기 어렵다",
            transform=ax.transAxes, fontsize=10.5, color=빨강)
    ax.set_xlabel("t값")
    ax.set_yticks([])
    ax.set_ylim(0, 0.45)
    ax.set_xlim(-5.2, 5.2)
    다듬기(ax)
    ax.spines["left"].set_visible(False)
    저장(fig, "ttest_null.png")
    return t값, p값, 자유도, 임계


# ------------------------------------------------------------------ 최소제곱
def 잔차그림():
    표 = 자료.dropna(subset=["상담횟수"])
    x, y = 표["상담횟수"].to_numpy(), 표["징벌횟수"].to_numpy()
    모형 = smf.ols("징벌횟수 ~ 상담횟수", data=표).fit()
    b0, b1 = 모형.params["Intercept"], 모형.params["상담횟수"]
    평균 = y.mean()
    SST = ((y - 평균) ** 2).sum()
    SSE = ((y - (b0 + b1 * x)) ** 2).sum()

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    for ax, 예측, 색, 제목 in [
        (axes[0], np.full_like(x, 평균, dtype=float), 회색, f"① 평균선(1.0)만 쓸 때\n잔차 제곱합 = {SST:.2f} (전체 변동)"),
        (axes[1], b0 + b1 * x, 빨강, f"② 회귀직선을 쓸 때\n잔차 제곱합 = {SSE:.2f} (설명하지 못한 변동)"),
    ]:
        for xi, yi, pi in zip(x, y, 예측):
            ax.plot([xi, xi], [yi, pi], color=색, lw=1.6, ls="--")
        if ax is axes[0]:
            ax.axhline(평균, color=진회색, lw=2)
        else:
            ax.plot([0, 8.5], [b0, b0 + b1 * 8.5], color=빨강, lw=2)
        ax.scatter(x, y, s=55, color=파랑, zorder=3)
        ax.annotate("2명", xy=(2, 2), xytext=(2.35, 2.35), fontsize=9, color=파랑)
        ax.set_title(제목, loc="left", fontsize=11.5)
        ax.set_xlabel("상담횟수")
        ax.set_xlim(-0.3, 8.8)
        ax.set_ylim(-1, 3.6)
        ax.axhline(0, color="#DDDDDD", lw=0.8, zorder=0)
        다듬기(ax)
    axes[0].set_ylabel("징벌횟수")
    axes[1].annotate("1002번: 잔차 = 0 - 0.67 = -0.67", xy=(5, 0.3), xytext=(4.3, 1.9), fontsize=9.5,
                     color=빨강, arrowprops=dict(arrowstyle="->", color=빨강, lw=0.8))
    fig.text(0.5, -0.04, f"점선이 잔차(실제 값 - 예측값). 최소제곱법은 잔차 제곱합이 가장 작은 직선을 고릅니다.   "
             f"$R^2$ = 1 - {SSE:.2f} / {SST:.0f} = {1 - SSE / SST:.2f}", ha="center", fontsize=10.5, color=진회색)
    fig.tight_layout()
    저장(fig, "ols_residuals.png")


# ------------------------------------------------------------------ 직선 vs 로지스틱
def 비교그림():
    선형 = smf.ols("징벌여부 ~ 나이", data=자료).fit()
    로짓 = smf.logit("징벌여부 ~ 나이", data=자료).fit(disp=0)
    a0, a1 = 선형.params["Intercept"], 선형.params["나이"]
    b0, b1 = 로짓.params["Intercept"], 로짓.params["나이"]
    나이축 = np.linspace(17, 66, 300)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax in axes:
        ax.axhspan(1, 1.45, color=빨강, alpha=0.07, lw=0)
        ax.axhspan(-0.45, 0, color=빨강, alpha=0.07, lw=0)
        ax.axhline(0, color=회색, lw=0.9, ls=":")
        ax.axhline(1, color=회색, lw=0.9, ls=":")
        ax.scatter(자료["나이"], 자료["징벌여부"], s=60, color=파랑, zorder=3)
        ax.set_xlim(17, 66)
        ax.set_ylim(-0.45, 1.45)
        ax.set_yticks([0, 0.5, 1])
        ax.set_xlabel("나이")
        다듬기(ax)
    axes[0].set_ylabel("징벌여부 (1 = 받음) / 예측 확률")

    axes[0].plot(나이축, a0 + a1 * 나이축, color=빨강, lw=2.2)
    axes[0].set_title("① 선형회귀 직선", loc="left", fontsize=12.5)
    axes[0].text(17.8, 1.3, "20대 초반: 예측값이 1보다 큼", fontsize=9.5, color=빨강)
    axes[0].text(65.2, -0.36, "60세 무렵: 0보다 작음", fontsize=9.5, color=빨강, ha="right")
    axes[0].text(41.5, 0.62, "확률로 읽을 수 없는\n값이 나옴", fontsize=10, color=진회색)

    axes[1].plot(나이축, 1 / (1 + np.exp(-(b0 + b1 * 나이축))), color=초록, lw=2.4)
    axes[1].set_title("② 로지스틱 곡선 (S자)", loc="left", fontsize=12.5)
    중간 = -b0 / b1
    axes[1].plot([중간, 중간], [-0.45, 0.5], color=회색, lw=0.9, ls="--")
    axes[1].plot([17, 중간], [0.5, 0.5], color=회색, lw=0.9, ls="--")
    axes[1].text(중간 + 0.8, 0.53, f"약 {중간:.0f}세에서 0.5", fontsize=9.5, color=진회색)
    axes[1].text(44, 0.8, "예측 확률이 항상\n0과 1 사이", fontsize=10, color=초록)

    fig.suptitle("징벌여부(0 또는 1)를 나이로 설명할 때, 어느 선으로 맞추시겠습니까?", x=0.02, ha="left",
                 fontsize=13.5, fontweight="bold")
    fig.tight_layout()
    저장(fig, "logit_vs_linear.png")


# ------------------------------------------------------------------ 시그모이드
def 시그모이드그림():
    로짓 = smf.logit("징벌여부 ~ 나이", data=자료).fit(disp=0)
    b0, b1 = 로짓.params["Intercept"], 로짓.params["나이"]

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"wspace": 0.35})
    ax = axes[0]
    나이축 = np.linspace(17, 66, 100)
    ax.plot(나이축, b0 + b1 * 나이축, color=파랑, lw=2.2)
    ax.axhline(0, color=회색, lw=0.9, ls=":")
    ax.set_title(r"① 일차식  $\eta = \beta_0 + \beta_1 \times$나이", loc="left", fontsize=12.5)
    ax.set_xlabel("나이")
    ax.set_ylabel(r"$\eta$ (로그 오즈)")
    ax.text(19, -4.3, "직선이라 위아래로 끝없이\n커지거나 작아질 수 있음", fontsize=10, color=진회색)
    다듬기(ax)

    ax = axes[1]
    η = np.linspace(-6.5, 6.5, 400)
    ax.plot(η, 1 / (1 + np.exp(-η)), color=초록, lw=2.4)
    ax.axhline(0, color=회색, lw=0.9, ls="--")
    ax.axhline(1, color=회색, lw=0.9, ls="--")
    for e, 글자위치 in ((-2, (-6.3, 0.24)), (0, (0.45, 0.39)), (2, (2.45, 0.77))):
        p = 1 / (1 + np.exp(-e))
        ax.scatter([e], [p], color=초록, s=40, zorder=3)
        ax.annotate(rf"$\eta$ = {e}  →  p = {p:.2f}", xy=(e, p), xytext=글자위치, fontsize=9.5)
    ax.text(-6.3, 0.94, r"$\eta$가 아무리 커도 1을 넘지 않음", fontsize=9.5, color=진회색)
    ax.text(6.3, 0.03, "아무리 작아도 0 아래로 가지 않음", fontsize=9.5, color=진회색, ha="right")
    ax.set_title(r"② 시그모이드 함수  $p = \dfrac{1}{1 + e^{-\eta}}$", loc="left", fontsize=12.5)
    ax.set_xlabel(r"$\eta$")
    ax.set_ylabel("p (확률)")
    ax.set_ylim(-0.08, 1.08)
    다듬기(ax)

    fig.text(0.49, 0.5, "→", fontsize=30, ha="center", va="center", color=진회색)
    fig.text(0.49, 0.38, "넣기", fontsize=10, ha="center", color=진회색)
    저장(fig, "sigmoid.png")


if __name__ == "__main__":
    print(t검정그림())
    잔차그림()
    비교그림()
    시그모이드그림()
