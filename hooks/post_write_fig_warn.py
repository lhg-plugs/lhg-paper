#!/usr/bin/env python3
"""lhg-paper 警告级 hook：写论文章节时，若插入了图片却没有配图题，提醒补图题。

触发：PostToolUse / Write|Edit。只看 sections/ 下的 markdown 文件。
检查：文件含 `![...](...)` 图片插入，但在图片附近 3 行内没有"图N：/表N："图题。

逃生：LHG_PAPER_HOOKS_OFF=1 关闭本 hook（与硬门共用一个开关）。
设计原则：只做提醒（additionalContext），从不拦截；内部出错 fail-open。
零第三方依赖。
"""

import json
import os
import re
import sys

IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
TITLE_RE = re.compile(r"(?:图|表)\s*[0-9一二三四五六七八九十]+[：:．.]")


def main() -> int:
    if os.environ.get("LHG_PAPER_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    fp = tool_input.get("file_path", "") or ""
    if not fp.lower().endswith((".md", ".markdown")):
        return 0
    if os.sep + "sections" + os.sep not in fp and "/sections/" not in fp:
        return 0
    if not os.path.isfile(fp):
        return 0

    try:
        with open(fp, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except Exception:
        return 0

    bad = 0
    for i, ln in enumerate(lines):
        if IMG_RE.search(ln):
            near = "\n".join(lines[i:i + 4])
            if not TITLE_RE.search(near):
                bad += 1
    if not bad:
        return 0

    out = {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext":
            "lhg-paper 提醒：%s 中有 %d 处图片插入缺少图题/编号（图N：……）。"
            "审稿人要求每张图都有自明的图题且在正文中被引用，"
            "建议跑 /lhg-paper:paper-figure 逐项核查。" % (os.path.basename(fp), bad)}}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
