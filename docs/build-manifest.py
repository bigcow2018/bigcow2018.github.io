#!/usr/bin/env python3
"""扫描 docs/files/，按名称末尾编号排序，生成 manifest.json 并更新 index.html 中的文件列表。

用法：在本目录或仓库根目录运行
    python3 docs/build-manifest.py

将 PDF 放入 files/（可建子目录）后再运行本脚本。页面将各子目录中的文件合并为一份清单，
不显示文件夹分组标题。排序依据文件名末尾编号：日期（YYYYMMDD）之后的序号按数值排列
（例如 100、101、102、103），位数可变。不要用纯字符串比较整个编号。
没有编号的条目按名称排在有编号的后面。仓库中的子目录结构保持不变。
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
FILES_DIR = ROOT / "files"
MANIFEST_PATH = ROOT / "manifest.json"
PAGE_PATH = ROOT / "index.html"
MARKER_START = "<!-- DOCS-LIST:START -->"
MARKER_END = "<!-- DOCS-LIST:END -->"
ID_RE = re.compile(r"(\d{8})(\d+)(?:\.[^.]+)?$")


def entry_key(name: str) -> tuple:
    match = ID_RE.search(name)
    if match:
        # (has-id, date, numeric sequence) so 100, 101, 102, 103 stay in value order
        return (0, match.group(1), int(match.group(2)), name)
    return (1, "", 0, name)


def file_id(name: str) -> str:
    match = ID_RE.search(name)
    return (match.group(1) + match.group(2)) if match else ""


def walk(dirpath: Path, rel: str = "") -> dict:
    dirs: list[dict] = []
    files: list[dict] = []
    if not dirpath.exists():
        raise SystemExit(f"找不到目录：{dirpath}")
    for path in dirpath.iterdir():
        if path.name.startswith("."):
            continue
        if path.is_dir():
            child_rel = f"{rel}/{path.name}" if rel else path.name
            dirs.append(walk(path, child_rel))
        elif path.is_file():
            files.append(
                {
                    "name": path.name,
                    "id": file_id(path.name),
                    "path": f"{rel}/{path.name}" if rel else path.name,
                    "bytes": path.stat().st_size,
                }
            )
    dirs.sort(key=lambda item: entry_key(item["name"]))
    files.sort(key=lambda item: entry_key(item["name"]))
    return {"name": dirpath.name if rel else "", "path": rel, "dirs": dirs, "files": files}


def fmt_size(n: int) -> str:
    if n >= 1048576:
        return f"{n / 1048576:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n} B"


def href_for(relpath: str) -> str:
    parts = [quote(part) for part in Path(relpath).parts]
    return "files/" + "/".join(parts)


def render_files(files: list[dict]) -> list[str]:
    lines = [
        '                    <div class="doc-list">',
        '                        <div class="doc-head">',
        '                            <span class="mono">编号</span>',
        "                            <span>文件名</span>",
        "                            <span>操作</span>",
        "                        </div>",
    ]
    for item in files:
        name = item["name"]
        ident = item["id"]
        href = href_for(item["path"])
        size = fmt_size(item["bytes"])
        ident_html = escape(ident) if ident else "—"
        lines.extend(
            [
                '                        <div class="doc-row">',
                f'                            <span class="bom-no">{ident_html}</span>',
                "                            <div>",
                f'                                <span class="doc-name">{escape(name)}</span>',
                f'                                <span class="doc-size mono">{escape(size)}</span>',
                "                            </div>",
                '                            <span class="doc-actions">',
                f'                                <a href="{escape(href, quote=True)}" download="{escape(name, quote=True)}">下载</a>',
                f'                                <a href="{escape(href, quote=True)}" target="_blank" rel="noopener">打开</a>',
                "                            </span>",
                "                        </div>",
            ]
        )
    lines.append("                    </div>")
    return lines


def flatten_files(node: dict) -> list[dict]:
    items = list(node["files"])
    for child in node["dirs"]:
        items.extend(flatten_files(child))
    items.sort(key=lambda item: entry_key(item["name"]))
    return items


def render_list(node: dict) -> list[str]:
    files = flatten_files(node)
    if not files:
        return ['                    <p class="doc-empty">暂无文档。</p>']
    return render_files(files)


def count_files(node: dict) -> int:
    return len(node["files"]) + sum(count_files(child) for child in node["dirs"])


def update_page(html: str, block: str) -> str:
    start = html.find(MARKER_START)
    end = html.find(MARKER_END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit("index.html 中缺少 DOCS-LIST 标记，无法更新列表。")
    start += len(MARKER_START)
    return html[:start] + "\n" + block + "\n                    " + html[end:]


def main() -> int:
    tree = walk(FILES_DIR)
    manifest = {
        "generated": date.today().isoformat(),
        "files_root": "files",
        "count": count_files(tree),
        "tree": tree,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    block = "\n".join(render_list(tree))
    page = PAGE_PATH.read_text(encoding="utf-8")
    PAGE_PATH.write_text(update_page(page, block), encoding="utf-8")
    print(f"已写入 {MANIFEST_PATH.relative_to(ROOT.parent)}，共 {manifest['count']} 个文件。")
    print(f"已更新 {PAGE_PATH.relative_to(ROOT.parent)} 中的列表。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
