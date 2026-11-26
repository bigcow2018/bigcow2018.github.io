#!/usr/bin/env python3
"""扫描 docs/files/，按名称末尾编号排序，生成 manifest.json 并更新 index.html 中的文件列表。

用法：在本目录或仓库根目录运行
    python3 docs/build-manifest.py

将 PDF 放入 files/（可建子目录）后再运行本脚本。排序依据文件或目录名末尾的
YYYYMMDDNNN（11 位数字）；没有编号的条目按名称排在有编号的后面。
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
ID_RE = re.compile(r"(\d{11})(?:\.[^.]+)?$")


def entry_key(name: str) -> tuple:
    match = ID_RE.search(name)
    if match:
        return (0, match.group(1), name)
    return (1, name, name)


def file_id(name: str) -> str:
    match = ID_RE.search(name)
    return match.group(1) if match else ""


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


def render_tree(node: dict, is_root: bool = True, indent: int = 20) -> list[str]:
    lines: list[str] = []
    pad = " " * indent
    if not is_root:
        ident = file_id(node["name"])
        ident_html = f'<span class="bom-no">{escape(ident)}</span> ' if ident else ""
        lines.append(f'{pad}<section class="doc-folder">')
        lines.append(
            f'{pad}    <h2 class="doc-folder-head">{ident_html}{escape(node["name"])}</h2>'
        )
        indent += 4
        pad = " " * indent
    if node["files"]:
        # render_files uses a fixed indent matching the root list; adjust if nested
        file_block = render_files(node["files"])
        if not is_root:
            file_block = [re.sub(r"^                    ", pad, line) for line in file_block]
        lines.extend(file_block)
    elif is_root and not node["dirs"]:
        lines.append(f'{pad}<p class="doc-empty">暂无文档。</p>')
    for child in node["dirs"]:
        lines.extend(render_tree(child, is_root=False, indent=indent))
    if not is_root:
        lines.append(f'{" " * (indent - 4)}</section>')
    return lines


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
    block = "\n".join(render_tree(tree, is_root=True))
    page = PAGE_PATH.read_text(encoding="utf-8")
    PAGE_PATH.write_text(update_page(page, block), encoding="utf-8")
    print(f"已写入 {MANIFEST_PATH.relative_to(ROOT.parent)}，共 {manifest['count']} 个文件。")
    print(f"已更新 {PAGE_PATH.relative_to(ROOT.parent)} 中的列表。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
