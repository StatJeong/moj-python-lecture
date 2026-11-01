"""강의용 코드 실행 움짤 생성기

파이썬 코드를 실제로 한 줄씩 실행하면서
  - 방금 실행한 줄
  - 그 줄 때문에 바뀐 변수 값 (함수 안의 변수는 따로 구역을 나눠 표시)
  - 화면 출력
을 한 장씩 그려 GIF로 저장한다. 프레임 PNG도 함께 저장해 슬라이드에 쓸 수 있다.

사용법
    python code_stepper.py 예제.py 결과.gif --title "for 반복문: 형기 합계"

추적 범위
    예제 파일 안에서 만든 함수는 호출, 안쪽 줄 실행, return까지 따라간다.
    print, round 같은 내장 함수와 외부 패키지 안쪽은 한 단계로 처리한다.
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
    out_bg="#F1F3F5", cap_bg="#EEF2F7", local_bg="#FFFFFF", local_border="#8FA3BF",
)
FILENAME = "<lecture>"


class FuncRef:
    """변수 칸에 '함수'로 표시하기 위한 표식."""

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, FuncRef) and other.name == self.name

    def __repr__(self):
        return "함수"


# ---------------------------------------------------------------- 실행 추적
def _snapshot(ns):
    snap = {}
    for k, v in list(ns.items()):
        if k.startswith("__") or isinstance(v, types.ModuleType):
            continue
        if isinstance(v, types.FunctionType):
            if v.__code__.co_filename == FILENAME:
                snap[k] = FuncRef(k)
            continue
        if callable(v):
            continue
        try:
            snap[k] = copy.deepcopy(v)
        except Exception:
            snap[k] = v
    return snap


def trace(code):
    """line / call / return 이벤트마다 변수 상태와 그때까지의 출력을 기록."""
    events, buf = [], io.StringIO()
    ns = {"__name__": "__main__"}
    compiled = compile(code, FILENAME, "exec")

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if event not in ("line", "call", "return"):
            return tracer
        is_mod = frame.f_code.co_name == "<module>"
        rec = dict(kind=event, line=frame.f_lineno, func=None if is_mod else frame.f_code.co_name,
                   g=_snapshot(frame.f_globals), l=None if is_mod else _snapshot(frame.f_locals),
                   out=buf.getvalue(), ret=None)
        if event == "return" and not is_mod:
            try:
                rec["ret"] = copy.deepcopy(arg)
            except Exception:
                rec["ret"] = arg
        if not (event == "call" and is_mod):
            events.append(rec)
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
            if isinstance(v, float):
                v = round(v, 4)
            return ast.copy_location(ast.Constant(v), node)
        return node


def substitute(expr, env):
    return ast.unparse(_Sub(env).visit(copy.deepcopy(expr)))


def _diff(before, after):
    return {k for k in after if k not in before or before[k] != after[k]}


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

        if isinstance(node, ast.FunctionDef):
            return f"함수 {node.name}() 만들기  →  안쪽 줄은 지금 실행하지 않고, 호출할 때 실행됨"

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
                src, sub = ast.unparse(rhs), substitute(rhs, before)
                if sub != src:
                    return f"{name} = {src}  →  {sub} = {new}"
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


def build_steps(events, ex):
    """이벤트 목록을 화면 한 장씩의 단계로 바꾼다."""
    steps, stack = [], []
    for i, e in enumerate(events):
        nxt = events[i + 1] if i + 1 < len(events) else None
        if nxt is None:
            break

        if e["kind"] == "line":
            if nxt["kind"] == "call":                      # 이 줄에서 함수를 부름
                stack.append(e)
                continue
            if nxt["kind"] == "return" and e["func"]:       # 함수의 마지막 줄
                node = ex.by_line.get(e["line"])
                if isinstance(node, ast.Return) and node.value is not None:
                    src, sub = ast.unparse(node.value), substitute(node.value, e["l"])
                    mid = f"  →  {sub}" if sub != src else ""
                    cap = f"return {src}{mid}  →  {fmt(nxt['ret'])}을(를) 돌려주고 함수 끝"
                else:
                    cap = ex.explain(e["line"], e["l"], nxt["l"], e["out"], nxt["out"], None) + ", 함수 끝"
                steps.append(dict(hl=e["line"], g=nxt["g"], l=nxt["l"], func=e["func"], out=nxt["out"],
                                  cap=cap, cg=set(), cl=_diff(e["l"], nxt["l"]), lists=ex.list_highlights()))
                continue
            # 같은 영역 안에서 다음 줄로
            if e["func"]:
                before, after = e["l"], nxt["l"]
            else:
                before, after = e["g"], nxt["g"]
            cap = ex.explain(e["line"], before, after, e["out"], nxt["out"], nxt["line"])
            steps.append(dict(hl=e["line"], g=nxt["g"], l=nxt["l"] if e["func"] else None, func=e["func"],
                              out=nxt["out"], cap=cap,
                              cg=set() if e["func"] else _diff(before, after),
                              cl=_diff(before, after) if e["func"] else set(), lists=ex.list_highlights()))

        elif e["kind"] == "call":
            caller = stack[-1]
            args = ", ".join(f"{k}={fmt(v)}" for k, v in e["l"].items())
            cap = f"함수 호출: {e['func']}({args})  →  값을 가지고 함수 안으로 들어감"
            steps.append(dict(hl=caller["line"], g=e["g"], l=e["l"], func=e["func"], out=e["out"], cap=cap,
                              cg=set(), cl=set(e["l"]), lists=ex.list_highlights()))

        elif e["kind"] == "return" and e["func"]:
            if nxt["kind"] == "call":                      # 같은 줄에서 또 다른 호출
                continue
            caller = stack.pop()
            if caller["func"]:
                before, after = caller["l"], nxt["l"]
            else:
                before, after = caller["g"], nxt["g"]
            node = ex.by_line.get(caller["line"])
            ret = fmt(e["ret"])
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                cap = f"돌려받은 값 {ret}  →  {name} = {fmt(after.get(name))}"
            elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                  and getattr(node.value.func, "id", "") == "print"):
                printed = nxt["out"][len(caller["out"]):].rstrip("\n")
                cap = f"돌려받은 값 {ret}  →  화면에 출력: {printed}"
            else:
                cap = f"돌려받은 값 {ret}  →  " + ex.explain(caller["line"], before, after,
                                                         caller["out"], nxt["out"], nxt["line"])
            steps.append(dict(hl=caller["line"], g=nxt["g"], l=nxt["l"] if caller["func"] else None,
                              func=caller["func"], out=nxt["out"], cap=cap,
                              cg=set() if caller["func"] else _diff(before, after),
                              cl=_diff(before, after) if caller["func"] else set(), lists=ex.list_highlights()))
    return steps


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


def _var_row(ax, k, v, y, vh, changed, list_hl, x0=0.548, w=0.432):
    if changed:
        ax.add_patch(Rectangle((x0 - 0.014, y - vh / 2 + 0.004), w, vh - 0.008, fc=C["changed"], ec="none"))
    ax.text(x0, y, k, family=CODE_FONT, size=15, color=C["text"], va="center")
    vx = 0.70
    if isinstance(v, (list, tuple)) and 0 < len(v) <= 8 and all(len(fmt(e)) <= 5 for e in v):
        _draw_list(ax, vx, y + 0.008, v, list_hl.get(k))
    else:
        ax.text(vx, y, fmt(v), family=CODE_FONT, size=16, color=C["text"], va="center")


def render(lines, title, step_label, step):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.945, title, family=TEXT_FONT, size=21, color=C["text"], va="center", weight="bold")
    ax.text(0.97, 0.945, step_label, family=TEXT_FONT, size=14, color=C["sub"], va="center", ha="right")

    # 코드
    _panel(ax, 0.03, 0.17, 0.47, 0.71, "코드 (노란 줄 = 방금 실행한 줄)")
    lh = min(0.07, 0.62 / max(len(lines), 1))
    y0 = 0.81
    for i, s in enumerate(lines, start=1):
        y = y0 - (i - 1) * lh
        if i == step["hl"]:
            ax.add_patch(Rectangle((0.034, y - lh / 2), 0.462, lh, fc=C["line_hl"], ec="none"))
            ax.plot([0.042], [y], marker=">", ms=10, color=C["mark"])
        ax.text(0.068, y, f"{i}", family=CODE_FONT, size=13, color=C["sub"], va="center", ha="right")
        ax.text(0.082, y, s, family=CODE_FONT, size=16, color=C["text"], va="center")

    # 변수
    g, loc, func = step["g"], step["l"], step["func"]
    show_local = func is not None and loc is not None
    out_h = 0.16 if show_local else 0.22
    var_y = 0.17 + out_h + 0.03
    _panel(ax, 0.53, var_y, 0.44, 0.88 - var_y, "변수 (방금 바뀐 값은 초록색)")
    n_rows = len(g) + (len(loc) + 1.6 if show_local else 0)
    vh = min(0.085, (0.88 - var_y - 0.06) / max(n_rows, 1))
    vy = 0.88 - 0.045 - vh / 2
    if not g and not show_local:
        ax.text(0.75, (var_y + 0.88) / 2, "아직 만든 변수가 없음", family=TEXT_FONT, size=14,
                color=C["sub"], ha="center")
    for k, v in g.items():
        _var_row(ax, k, v, vy, vh, k in step["cg"], step["lists"])
        vy -= vh
    if show_local:
        top = vy + vh / 2 - 0.01
        box_h = vh * (len(loc) + 0.6) + 0.03
        ax.add_patch(FancyBboxPatch((0.545, top - box_h), 0.41, box_h, boxstyle="round,pad=0,rounding_size=0.006",
                                    fc=C["local_bg"], ec=C["local_border"], lw=1.4, ls="--"))
        ax.text(0.555, top - 0.006, f"{func}() 안의 변수 (함수가 끝나면 사라짐)", family=TEXT_FONT, size=11,
                color=C["sub"], va="top")
        vy = top - 0.03 - vh / 2
        for k, v in loc.items():
            _var_row(ax, k, v, vy, vh, k in step["cl"], step["lists"], x0=0.562, w=0.39)
            vy -= vh

    # 출력
    _panel(ax, 0.53, 0.17, 0.44, out_h, "출력", face=C["out_bg"])
    n_out = 3 if show_local else 4
    out_lines = step["out"].rstrip("\n").split("\n")[-n_out:] if step["out"].strip() else []
    for j, s in enumerate(out_lines):
        ax.text(0.548, 0.17 + out_h - 0.065 - j * 0.04, s, family=CODE_FONT, size=14, color=C["text"], va="center")

    # 설명
    ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.11, boxstyle="round,pad=0,rounding_size=0.008",
                                fc=C["cap_bg"], ec="none"))
    ax.text(0.05, 0.085, "\n".join(textwrap.wrap(step["cap"], 72)), family=TEXT_FONT, size=16,
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
    ex = Explainer(code)
    steps = build_steps(trace(code), ex)

    n = len(steps)
    first = dict(hl=None, g={}, l=None, func=None, out="", cap="실행 전: 코드는 위에서 아래로, 한 줄씩 실행됩니다",
                 cg=set(), cl=set(), lists={})
    frames = [render(lines, title, f"0 / {n}", first)]
    for k, st in enumerate(steps, start=1):
        frames.append(render(lines, title, f"{k} / {n}", st))

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
