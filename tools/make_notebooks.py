"""qmd 원고를 Colab 실습 노트북(ipynb)으로 바꾼다.

    python tools/make_notebooks.py

- 파이썬 코드 블록은 코드 셀, 나머지는 글 셀이 된다 (## 제목마다 글 셀을 나눈다).
- 코드 블록 앞의 #| 옵션 줄은 지운다.
- <details> ... </details> 안의 정답은 노트북에 넣지 않는다 (빈 칸에서 직접 풀도록).
- 그림과 움짤(images/)은 노트북에 넣지 않고, 웹 강의자료에서 보라는 안내 한 줄로 바꾼다.
- ::: {.callout-...} 블록은 "[주의] 제목" 형태의 인용문으로 바꾼다 (Colab에는 콜아웃 상자가 없어서).
- 맨 위 "Colab에서 열기" 링크 줄은 웹 강의자료 링크로 바꾼다.
"""

import re
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = "StatJeong/moj-python-lecture"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
SITE = "https://statjeong.github.io/moj-python-lecture/"
ROOT = Path(__file__).resolve().parent.parent
CALLOUT_LABEL = {"note": "참고", "warning": "주의", "tip": "팁", "important": "중요", "caution": "조심"}
CHAPTERS = ["01_python_basics", "02_pandas", "03_visualization", "04_statistics", "05_ai", "06_yearbook"]


def parse(text):
    """front matter 제목과 (종류, 내용) 블록 목록을 돌려준다."""
    title = ""
    if text.startswith("---"):
        _, fm, text = text.split("---", 2)
        m = re.search(r'title:\s*"?(.*?)"?\s*$', fm, re.M)
        title = m.group(1) if m else ""

    blocks, md, code = [], [], None
    in_details = False
    callout = None                                 # 콜아웃 블록 안이면 [종류, 제목]
    for line in text.splitlines():
        s = line.strip()
        if callout is not None:                    # 콜아웃 안: 인용문(>)으로 바꾼다
            if s == ":::":
                callout = None
                md.append("")
            else:
                md.append(("> " + line).rstrip() if s else ">")
            continue
        m = re.match(r'^:::\s*\{\.callout-(\w+)(?:[^}]*?title="([^"]*)")?[^}]*\}', s)
        if m and code is None and not in_details:
            label = CALLOUT_LABEL.get(m.group(1), "참고")
            head = f"[{label}] {m.group(2)}" if m.group(2) else f"[{label}]"
            md.append(f"> {head}")
            md.append(">")
            callout = m.group(1)
            continue
        if code is not None:                       # 코드 블록 안
            if s == "```":
                if not in_details:
                    body = [c for c in code if not c.startswith("#|")]
                    blocks.append(("code", "\n".join(body).strip("\n")))
                code = None
            else:
                code.append(line)
            continue
        if s.startswith("<details"):
            in_details = True
            continue
        if s.startswith("</details"):
            in_details = False
            continue
        if in_details:
            if s.startswith("```{python}"):
                code = []
            continue
        if s.startswith("```{python}"):
            if md:
                blocks.append(("md", "\n".join(md)))
                md = []
            code = []
            continue
        if s.startswith("## ") and md:
            blocks.append(("md", "\n".join(md)))
            md = []
        md.append(line)
    if md:
        blocks.append(("md", "\n".join(md)))
    return title, blocks


def fix_markdown(src, name):
    # 그림과 움짤은 웹 강의자료에만 둔다. 노트북에는 안내 한 줄만 남긴다.
    src = re.sub(r"^!\[([^\]]*)\]\(images/[^)]+\)[ \t]*$",
                 lambda m: f"(그림: {m.group(1)} - 웹 강의자료 [{SITE}{name}.html]({SITE}{name}.html)에서 볼 수 있습니다)",
                 src, flags=re.M)
    src = re.sub(r"\]\(([0-9]{2}_[a-z_]+)\.qmd\)", lambda m: f"]({SITE}{m.group(1)}.html)", src)
    src = re.sub(r"^\[Colab에서 실습 노트북 열기\]\(.*\)$",
                 f"웹 강의자료: [{SITE}{name}.html]({SITE}{name}.html)", src, flags=re.M)
    return src.strip("\n")


def build(name):
    text = (ROOT / f"{name}.qmd").read_text(encoding="utf-8")
    title, blocks = parse(text)
    cells = [new_markdown_cell(f"# {title}")]
    for kind, content in blocks:
        if kind == "code":
            if content:
                cells.append(new_code_cell(content))
        else:
            content = fix_markdown(content, name)
            if content.strip():
                cells.append(new_markdown_cell(content))
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["colab"] = {"provenance": [], "toc_visible": True}
    out = ROOT / "notebooks" / f"{name}.ipynb"
    out.parent.mkdir(exist_ok=True)
    nbformat.write(nb, out)
    n_code = sum(c.cell_type == "code" for c in cells)
    print(f"{out.relative_to(ROOT)}: 셀 {len(cells)}개 (코드 {n_code}개)")


if __name__ == "__main__":
    for ch in CHAPTERS:
        build(ch)
