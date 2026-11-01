"""강의용: pd.merge가 행마다 짝을 찾아 붙이는 과정을 GIF로 그린다.

사용법
    python merge_anim.py 수용자.csv 시설현황.csv 결과.gif
"""

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from code_stepper import CODE_FONT, TEXT_FONT, C  # noqa: E402

W, H, DPI = 12.8, 7.2, 100
HDR, KEY, GRAY = "#E5E9F0", "#D6E4F5", "#EEEEEE"
RH, Y_HDR = 0.055, 0.775


def table(ax, x, label, cols, widths, rows, hl=None, gray=None, key="시설", empty_rows=0):
    ax.text(x, Y_HDR + 0.05, label, family=TEXT_FONT, size=14, color=C["text"], va="center", weight="bold")
    cx = x
    for c, w in zip(cols, widths):
        ax.add_patch(Rectangle((cx, Y_HDR - RH / 2), w, RH, fc=KEY if c == key else HDR, ec=C["border"]))
        ax.text(cx + w / 2, Y_HDR, c, family=TEXT_FONT, size=12, ha="center", va="center", color=C["text"])
        cx += w
    for r, row in enumerate(rows):
        y = Y_HDR - (r + 1) * RH
        cx = x
        for v, w in zip(row, widths):
            fc = C["line_hl"] if r == hl else (GRAY if r == gray else "white")
            ax.add_patch(Rectangle((cx, y - RH / 2), w, RH, fc=fc, ec=C["border"]))
            ax.text(cx + w / 2, y, "" if v is None else str(v), family=CODE_FONT, size=12, ha="center",
                    va="center", color=C["sub"] if r == gray else C["text"])
            cx += w
    for r in range(len(rows), len(rows) + empty_rows):
        y = Y_HDR - (r + 1) * RH
        ax.add_patch(Rectangle((x, y - RH / 2), sum(widths), RH, fc="white", ec=C["border"], ls=":"))


def row_y(r):
    return Y_HDR - (r + 1) * RH


def frame(left, right, result_rows, n_total, code_lines, caption, hl_l=None, hl_r=None, gray_r=None,
          with_rate=False, note_r=None):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.955, "pd.merge: 시설 열을 기준으로 두 표 합치기", family=TEXT_FONT, size=20,
            weight="bold", color=C["text"], va="center")
    for i, s in enumerate(code_lines):
        ax.text(0.03, 0.905 - i * 0.035, s, family=CODE_FONT, size=13, color=C["text"], va="center")

    lx, lw = 0.03, [0.085, 0.095]
    rx, rw = 0.29, [0.095, 0.07, 0.07]
    ox = 0.585
    ow = [0.075, 0.085, 0.06, 0.06] + ([0.07] if with_rate else [])
    ocols = ["수용번호", "시설", "정원", "현원"] + (["수용률"] if with_rate else [])

    table(ax, lx, "수용자 (일부 열)", ["수용번호", "시설"], lw, left, hl=hl_l)
    table(ax, rx, "시설현황", ["시설", "정원", "현원"], rw, right, hl=hl_r, gray=gray_r)
    table(ax, ox, f"합친표 ({len(result_rows)}행)", ocols, ow, result_rows,
          hl=len(result_rows) - 1 if hl_l is not None else None, empty_rows=n_total - len(result_rows))

    if note_r is not None:
        ax.text(rx + sum(rw) / 2, row_y(note_r) - RH * 0.95, "수용자 표에 없음 → 붙을 곳 없음",
                family=TEXT_FONT, size=11, color=C["sub"], ha="center", va="center")

    if hl_l is not None and hl_r is not None:
        y1, y2 = row_y(hl_l), row_y(hl_r)
        ax.annotate("", xy=(rx - 0.004, y2), xytext=(lx + sum(lw) + 0.004, y1),
                    arrowprops=dict(arrowstyle="->", color=C["mark"], lw=2))
        y3 = row_y(len(result_rows) - 1)
        ax.annotate("", xy=(ox - 0.004, y3), xytext=(rx + sum(rw) + 0.004, y2),
                    arrowprops=dict(arrowstyle="->", color=C["mark"], lw=2))

    ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.1, boxstyle="round,pad=0,rounding_size=0.008",
                                fc=C["cap_bg"], ec="none"))
    ax.text(0.05, 0.08, caption, family=TEXT_FONT, size=15, color=C["text"], va="center")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def main(inmate_csv, facility_csv, out_gif, frames_dir=None):
    a = pd.read_csv(inmate_csv)
    b = pd.read_csv(facility_csv)
    m = pd.merge(a, b, on="시설")
    m["수용률"] = (m["현원"] / m["정원"] * 100).round(1)

    left = a[["수용번호", "시설"]].values.tolist()
    right = b[["시설", "정원", "현원"]].values.tolist()
    fac_idx = {f: i for i, f in enumerate(b["시설"])}
    unmatched = [i for i, f in enumerate(b["시설"]) if f not in set(a["시설"])]
    n = len(m)
    code1 = ['합친표 = pd.merge(수용자, 시설현황, on="시설")']
    code2 = code1 + ['합친표["수용률"] = (합친표["현원"] / 합친표["정원"] * 100).round(1)']

    frames, durs = [], []
    frames.append(frame(left, right, [], n, code1,
                        "두 표에 모두 있는 '시설' 열(파란 칸)을 기준으로, 수용자 한 명씩 시설현황에서 짝을 찾아 붙입니다"))
    durs.append(3500)

    for i in range(n):
        rows = m[["수용번호", "시설", "정원", "현원"]].values.tolist()[: i + 1]
        num, fac, cap_, cur = rows[-1]
        j = fac_idx[fac]
        frames.append(frame(left, right, rows, n, code1,
                            f"{num}번의 시설은 {fac}  →  시설현황의 {fac} 행에서 정원 {cap_}, 현원 {cur}을 가져와 붙임",
                            hl_l=i, hl_r=j))
        durs.append(2200 if i < 2 else 1300)

    full = m[["수용번호", "시설", "정원", "현원"]].values.tolist()
    g = unmatched[0] if unmatched else None
    frames.append(frame(left, right, full, n, code1,
                        f"짝이 없는 시설은 결과에 들어가지 않음  →  합친표는 수용자 수와 같은 {n}행",
                        gray_r=g, note_r=g))
    durs.append(4000)

    full_rate = m[["수용번호", "시설", "정원", "현원", "수용률"]].values.tolist()
    frames.append(frame(left, right, full_rate, n, code2,
                        "같은 행에 정원과 현원이 함께 있으니 수용률을 바로 계산할 수 있음", with_rate=True))
    durs.append(5000)

    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(out_gif, save_all=True, append_images=pal[1:], duration=durs, loop=0)
    if frames_dir:
        d = Path(frames_dir)
        d.mkdir(parents=True, exist_ok=True)
        for k, f in enumerate(frames):
            f.save(d / f"{k:02d}.png")
    print(f"{out_gif}: {len(frames)} frames")


if __name__ == "__main__":
    main(*sys.argv[1:4], frames_dir=sys.argv[4] if len(sys.argv) > 4 else None)
