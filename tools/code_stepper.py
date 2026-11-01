"""강의용 코드 실행 움짤 생성기

파이썬 코드를 실제로 한 줄씩 실행하면서
  - 방금 실행한 줄
  - 그 줄 때문에 바뀐 변수 값
  - 화면 출력
을 한 장씩 그려 GIF로 저장한다. 프레임 PNG도 함께 저장해 슬라이드에 쓸 수 있다.

사용법
    python code_stepper.py 예제.py 결과.gif --title "for 반복문: 형기 합계"

제한
    모듈 최상단 코드만 추적한다 (함수 내부는 한 단계로 처리).
"""

import argparse
import ast
import contextlib
import copy
import io
import sys
import textwrap
import types
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402


def _pick_font(candidates):
    names = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in names:
            return c
    return "DejaVu Sans"


CODE_FONT = _pick_font(["Noto Sans Mono CJK KR", "NanumGothicCoding", "D2Coding", "Noto Sans Mono CJK JP"])
TEXT_FONT = _pick_font(["Noto Sans CJK KR", "NanumGothic", "Malgun Gothic", "AppleGothic", "Noto Sans CJK JP"])

W, H, DPI = 12.8, 7.2, 100
C = dict(
    text="#1F2328", sub="#6B7280", panel="#F6F7F9", border="#D0D5DD",
    line_hl="#FFE9A8", mark="#B7791F", changed="#DCEFDD",
    elem="#FFFFFF", elem_hl="#FFE9A8", elem_border="#9AA3AF", elem_border_hl="#B7791F",
    out_bg="#F1F3F5", cap_bg="#EEF2F7",
)
FILENAME = "<lecture>"


# ---------------------------------------------------------------- 실행 추적
def _snapshot(ns):
    snap = {}
    for k, v in ns.items():
        if k.startswith("__") or callable(v) or isinstance(v, types.ModuleType):
            continue
        try:
            snap[k] = copy.deepcopy(v)
        except Exception:
            snap[k] = v
    return snap


def trace(code):
    """실행되는 줄마다 (줄 번호, 그 줄 실행 직전 변수, 그때까지의 출력)을 기록."""
    events, buf = [], io.StringIO()
    ns = {"__name__": "__main__"}
    compiled = compile(code, FILENAME, "exec")

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME or frame.f_code.co_name != "<module>":
            return None
        if event == "line":
            events.append(dict(line=frame.f_lineno, vars=_snapshot(frame.f_globals), out=buf.getvalue()))
        elif event == "return":
            events.append(dict(line=None, vars=_snapshot(frame.f_globals), out=buf.getvalue()))
        return tracer

    with contextlib.redirect_stdout(buf):
        sys.settrace(tracer)
        try:
            exec(compiled, ns)
        finally:
            sys.settrace(None)
    return events


# ---------------------------------------------------------------- 설명 문장
def fmt(v):
    if isinstance(v, float):
        return f"{v:.4g}"
    return repr(v) if isinstance(v, str) else str(v)


class _Sub(ast.NodeTransformer):
    def __init__(self, env):
        self.env = env

    def visit_Name(self, node):
        v = self.env.get(node.id, None)
        if isinstance(node.ctx, ast.Load) and isinstance(v, (int, float, str, bool)) and node.id in self.env:
            return ast.copy_location(ast.Constant(v), node)
        return node


def substitute(expr, env):
    return ast.unparse(_Sub(env).visit(copy.deepcopy(expr)))


class Explainer:
    def __init__(self, code):
        self.tree = ast.parse(code)
        self.by_line = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.stmt):
                self.by_line.setdefault(node.lineno, node)
        self.loop_count = {}
        self.active = {}  # for 줄 번호 -> (반복 대상 변수명, 현재 위치)

    @staticmethod
    def _body_lines(node):
        return range(node.body[0].lineno, node.end_lineno + 1)

    def explain(self, line, before, after, out_before, out_after, next_line):
        node = self.by_line.get(line)

        if isinstance(node, ast.For):
            tgt, it = ast.unparse(node.target), ast.unparse(node.iter)
            if next_line in self._body_lines(node):
                n = self.loop_count.get(line, 0) + 1
                self.loop_count[line] = n
                if isinstance(node.iter, ast.Name):
                    self.active[line] = (node.iter.id, n - 1)
                return f"반복 {n}회째: {it}에서 다음 값을 꺼냄  →  {tgt} = {fmt(after.get(tgt))}"
            self.loop_count[line] = 0
            self.active.pop(line, None)
            return f"{it}에서 더 꺼낼 값이 없음  →  반복을 끝내고 다음 줄로"

        if isinstance(node, (ast.If, ast.While)):
            src, sub = ast.unparse(node.test), substitute(node.test, before)
            try:
                val = bool(eval(compile(ast.Expression(node.test), "<t>", "eval"), {}, dict(before)))
            except Exception:
                val = next_line in self._body_lines(node)
            mid = f"  →  {sub}" if sub != src else ""
            res = "참(True)" if val else "거짓(False)"
            if isinstance(node, ast.While):
                tail = "반복 계속" if val else "반복 끝"
            else:
                tail = "들여쓴 줄을 실행" if val else "들여쓴 줄을 건너뜀"
            return f"조건 확인: {src}{mid}  →  {res}, {tail}"

        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name, rhs = node.targets[0].id, node.value
            new = fmt(after.get(name))
            if name not in before:
                return f"새 변수 {name} 만들기  →  {name} = {new}"
            src, sub = ast.unparse(rhs), substitute(rhs, before)
            if sub != src:
                return f"{name} = {src}  →  {sub} = {new}"
            return f"{name} 값 바꾸기: {fmt(before[name])}  →  {new}"

        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            return f"{ast.unparse(node)}  →  {name}: {fmt(before.get(name))} → {fmt(after.get(name))}"

        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", "") == "print"):
            printed = out_after[len(out_before):].rstrip("\n")
            return f"화면에 출력  →  {printed}"

        changed = [k for k in after if k not in before or before[k] != after[k]]
        if changed:
            return "실행  →  " + ", ".join(f"{k} = {fmt(after[k])}" for k in changed)
        return "실행"

    def list_highlights(self):
        return {name: idx for name, idx in self.active.values()}


# ---------------------------------------------------------------- 그리기
def _panel(ax, x, y, w, h, label, face=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.008",
                                fc=face or C["panel"], ec=C["border"], lw=1.2))
    ax.text(x + 0.012, y + h - 0.012, label, family=TEXT_FONT, size=12, color=C["sub"], va="top")


def _draw_list(ax, x, y, values, hl_idx):
    bw, bh = 0.052, 0.05
    for i, v in enumerate(values):
        on = i == hl_idx
        ax.add_patch(Rectangle((x + i * (bw + 0.006), y - bh / 2), bw, bh,
                               fc=C["elem_hl"] if on else C["elem"],
                               ec=C["elem_border_hl"] if on else C["elem_border"], lw=2 if on else 1))
        ax.text(x + i * (bw + 0.006) + bw / 2, y, fmt(v), family=CODE_FONT, size=14,
                ha="center", va="center", color=C["text"])
        ax.text(x + i * (bw + 0.006) + bw / 2, y - bh / 2 - 0.018, str(i), family=CODE_FONT,
                size=10, ha="center", va="center", color=C["sub"])


def render(lines, title, step_label, hl_line, vars_now, changed, list_hl, output, caption):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.945, title, family=TEXT_FONT, size=21, color=C["text"], va="center", weight="bold")
    ax.text(0.97, 0.945, step_label, family=TEXT_FONT, size=14, color=C["sub"], va="center", ha="right")

    # 코드
    _panel(ax, 0.03, 0.17, 0.47, 0.71, "코드 (노란 줄 = 방금 실행한 줄)")
    lh = min(0.07, 0.58 / max(len(lines), 1))
    y0 = 0.80
    for i, s in enumerate(lines, start=1):
        y = y0 - (i - 1) * lh
        if i == hl_line:
            ax.add_patch(Rectangle((0.034, y - lh / 2), 0.462, lh, fc=C["line_hl"], ec="none"))
            ax.plot([0.042], [y], marker=">", ms=10, color=C["mark"])
        ax.text(0.068, y, f"{i}", family=CODE_FONT, size=13, color=C["sub"], va="center", ha="right")
        ax.text(0.082, y, s, family=CODE_FONT, size=16, color=C["text"], va="center")

    # 변수
    _panel(ax, 0.53, 0.42, 0.44, 0.46, "변수 (방금 바뀐 값은 초록색)")
    vy, vh = 0.80, 0.085
    if not vars_now:
        ax.text(0.75, 0.65, "아직 만든 변수가 없음", family=TEXT_FONT, size=14, color=C["sub"], ha="center")
    for k, v in vars_now.items():
        if k in changed:
            ax.add_patch(Rectangle((0.534, vy - vh / 2 + 0.005), 0.432, vh - 0.01, fc=C["changed"], ec="none"))
        ax.text(0.548, vy, k, family=CODE_FONT, size=15, color=C["text"], va="center")
        vx = 0.70
        if isinstance(v, (list, tuple)) and 0 < len(v) <= 8 and all(len(fmt(e)) <= 5 for e in v):
            _draw_list(ax, vx, vy + 0.008, v, list_hl.get(k))
        else:
            ax.text(vx, vy, fmt(v), family=CODE_FONT, size=16, color=C["text"], va="center")
        vy -= vh

    # 출력
    _panel(ax, 0.53, 0.17, 0.44, 0.22, "출력", face=C["out_bg"])
    out_lines = output.rstrip("\n").split("\n")[-4:] if output.strip() else []
    for j, s in enumerate(out_lines):
        ax.text(0.548, 0.32 - j * 0.04, s, family=CODE_FONT, size=14, color=C["text"], va="center")

    # 설명
    ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.11, boxstyle="round,pad=0,rounding_size=0.008",
                                fc=C["cap_bg"], ec="none"))
    ax.text(0.05, 0.085, "\n".join(textwrap.wrap(caption, 62)), family=TEXT_FONT, size=16,
            color=C["text"], va="center")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# ---------------------------------------------------------------- 조립
def make_gif(code, out_path, title, step_ms=1800, first_ms=2200, last_ms=4500, frames_dir=None):
    code = textwrap.dedent(code).strip("\n")
    lines = code.split("\n")
    events = trace(code)
    ex = Explainer(code)

    n_steps = len(events) - 1
    frames = [render(lines, title, f"0 / {n_steps}", None, {}, set(), {}, "",
                     "실행 전: 코드는 위에서 아래로, 한 줄씩 실행됩니다")]
    for k in range(1, len(events)):
        prev, cur = events[k - 1], events[k]
        cap = ex.explain(prev["line"], prev["vars"], cur["vars"], prev["out"], cur["out"], cur["line"])
        changed = {n for n in cur["vars"] if n not in prev["vars"] or prev["vars"][n] != cur["vars"][n]}
        frames.append(render(lines, title, f"{k} / {n_steps}", prev["line"], cur["vars"], changed,
                             ex.list_highlights(), cur["out"], cap))

    durations = [first_ms] + [step_ms] * (len(frames) - 2) + [last_ms]
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(out_path, save_all=True, append_images=pal[1:], duration=durations, loop=0)

    if frames_dir:
        d = Path(frames_dir)
        d.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(frames):
            f.save(d / f"{i:02d}.png")
    return len(frames)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("code_file")
    p.add_argument("out_gif")
    p.add_argument("--title", default="코드 실행 과정")
    p.add_argument("--step-ms", type=int, default=1800)
    p.add_argument("--frames-dir")
    a = p.parse_args()
    n = make_gif(Path(a.code_file).read_text(encoding="utf-8"), a.out_gif, a.title, a.step_ms,
                 frames_dir=a.frames_dir)
    print(f"{a.out_gif}: {n} frames")


if __name__ == "__main__":
    main()
