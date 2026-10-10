#!/usr/bin/env python3
"""lhg-paper 投稿前自查审计脚本：引用 / 图表 / 摘要 / 关键词 / 口语化 / 伦理声明。

论文目录约定：
    paper/
    ├── paper.yaml            # 可选（题目/作者/目标期刊）
    ├── sections/             # 一节一 md：01-abstract.md, 02-introduction.md ...
    ├── references.bib        # BibTeX 参考文献（或 references.md）
    └── figures/              # 图片（可选）

用法：
    python3 paper_audit.py --target <论文目录> [--format json|text]
退出码：有 blocker → 1；否则 → 0。纯 Python 标准库，零第三方依赖。
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- 规则注册表
# 每条规则：(rule_id, 标题, 级别, 检查函数(ctx) -> [finding...])
# finding: {"rule_id","severity","file","title","detail"}

CITE_KEY_RE = re.compile(r"\[@([A-Za-z0-9_:\-]+)\]")
CITE_NUM_RE = re.compile(r"\[(?:[1-9]\d*(?:\s*[,，\-–—]\s*[1-9]\d*)*)\]")
FIG_MENTION_RE = re.compile(r"[图圖表表]\s*([0-9一二三四五六七八九十]+)")
FIG_TITLE_RE = re.compile(r"^[> \t]*(?:图|表)\s*[0-9一二三四五六七八九十]+[：:．.]", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
COLLOQUIAL = ["我觉得", "我认为", "非常", "超级", "相当", "很显然", "基本上",
              "众所周知", "显而易见", "很简单", "容易地", "令人震惊",
              " guys", "kind of", "sort of", "very very"]
ETHICS_WORDS = ["利益冲突", "conflict of interest", "伦理审查", "伦理委员会",
                "ethics approval", "知情同意"]
REQUIRED_SECTIONS = [("引言", ("引言", "介绍", "introduction")),
                     ("方法", ("方法", "methods", "method")),
                     ("结果", ("结果", "results", "result")),
                     ("讨论", ("讨论", "discussion"))]


def F(rule_id, severity, title, file, detail):
    return {"rule_id": rule_id, "severity": severity, "title": title,
            "file": file, "detail": detail}


def tok_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", text))


# ---------------------------------------------------------------- 上下文
class Ctx:
    def __init__(self, target):
        self.target = target
        self.sections_dir = os.path.join(target, "sections")
        self.files = {}   # relpath -> text
        if os.path.isdir(self.sections_dir):
            for fn in sorted(os.listdir(self.sections_dir)):
                if fn.lower().endswith((".md", ".markdown", ".tex")):
                    p = os.path.join(self.sections_dir, fn)
                    try:
                        with open(p, encoding="utf-8") as f:
                            self.files["sections/" + fn] = f.read()
                    except Exception:
                        pass
        self.bib_path = None
        for cand in ("references.bib", "references.md"):
            p = os.path.join(target, cand)
            if os.path.isfile(p):
                self.bib_path = p
                try:
                    with open(p, encoding="utf-8") as f:
                        self.files[cand] = f.read()
                except Exception:
                    pass
        self.all_text = "\n".join(self.files.values())

    def bib_keys(self):
        keys = set()
        if self.bib_path and self.bib_path.endswith(".bib"):
            keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,",
                                  self.files.get("references.bib", "")))
        return keys

    def section_text(self, *name_hints):
        for rel, text in self.files.items():
            low = rel.lower()
            if any(h in rel or h in low for h in name_hints):
                return rel, text
        return None, ""


# ---------------------------------------------------------------- 规则实现
def r_absent(ctx):
    rel, text = ctx.section_text("abstract", "摘要")
    if rel is None:
        return [F("PP-ABS-001", "blocker", "摘要缺失",
                   "sections/", "未找到摘要文件（01-abstract.md / 摘要.md）")]
    if tok_count(text) < 30:
        return [F("PP-ABS-001", "blocker", "摘要过短/近乎空白", rel,
                   "摘要正文不足 30 词，疑似缺失")]
    return []


def r_abstract_long(ctx):
    rel, text = ctx.section_text("abstract", "摘要")
    if rel is None:
        return []
    n = tok_count(text)
    if n > 350:
        return [F("PP-ABS-002", "warning", "摘要超长", rel,
                   "摘要约 %d 词，超过 350 词上限建议（以目标期刊为准）" % n)]
    return []


def r_keywords(ctx):
    rel, text = ctx.section_text("abstract", "摘要")
    if rel is None:
        return []
    if not re.search(r"关键词|key\s*words?", text, re.I):
        return [F("PP-KW-001", "blocker", "关键词缺失", rel,
                   "摘要未给出关键词行（格式如：关键词：A；B；C）")]
    return []


def r_sections(ctx):
    missing = []
    for label, hints in REQUIRED_SECTIONS:
        rel, text = ctx.section_text(*hints)
        if rel is None or tok_count(text) < 50:
            missing.append(label)
    if missing:
        return [F("PP-SEC-001", "blocker", "核心章节缺失",
                   "sections/", "缺少或近乎空白：%s（需要引言/方法/结果/讨论）"
                   % "、".join(missing))]
    return []


def r_cite_ghost(ctx):
    keys_used = set()
    for rel, text in ctx.files.items():
        if rel.startswith("sections/"):
            keys_used |= set(CITE_KEY_RE.findall(text))
    findings = []
    if not ctx.bib_path:
        if keys_used or CITE_NUM_RE.search(ctx.all_text):
            findings.append(F("PP-CITE-001", "blocker", "引用无参考文献文件",
                              ctx.target, "正文出现引用标记，但未找到 references.bib"))
        return findings
    bib_keys = ctx.bib_keys()
    for k in sorted(keys_used - bib_keys)[:10]:
        findings.append(F("PP-CITE-001", "blocker", "幽灵引用", "references.bib",
                          "正文引用 [@%s] 在参考文献中不存在" % k))
    # bib 条目必填字段
    if ctx.bib_path.endswith(".bib"):
        bib = ctx.files.get("references.bib", "")
        for m in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=@\w+\s*\{|\Z)",
                             bib, re.S):
            key, body = m.group(1), m.group(2).lower()
            lack = [f for f in ("author", "title", "year")
                    if f not in body]
            if lack:
                findings.append(F("PP-CITE-001", "blocker", "参考文献条目字段缺失",
                                  "references.bib",
                                  "条目 %s 缺少：%s" % (key, "、".join(lack))))
    return findings


def r_cite_dangling(ctx):
    if not ctx.bib_path or not ctx.bib_path.endswith(".bib"):
        return []
    keys_used = set()
    for rel, text in ctx.files.items():
        if rel.startswith("sections/"):
            keys_used |= set(CITE_KEY_RE.findall(text))
    findings = []
    for k in sorted(ctx.bib_keys() - keys_used)[:10]:
        findings.append(F("PP-CITE-002", "warning", "悬挂文献", "references.bib",
                          "条目 %s 从未被正文引用，确认是否多余" % k))
    return findings


def _norm_num(s):
    cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if s.isdigit():
        return int(s)
    return cn.get(s, -1)


def r_fig_missing(ctx):
    mentioned = set()
    for rel, text in ctx.files.items():
        if rel.startswith("sections/"):
            for m in FIG_MENTION_RE.finditer(text):
                n = _norm_num(m.group(1))
                if n > 0:
                    mentioned.add((m.group(0)[0], n))
    defined = set()
    for m in FIG_TITLE_RE.finditer(ctx.all_text):
        mm = re.match(r"[> \t]*(?:图|表)\s*([0-9一二三四五六七八九十]+)", m.group(0))
        if mm:
            n = _norm_num(mm.group(1))
            if n > 0:
                defined.add((m.group(0).strip()[0], n))
    findings = []
    for kind, n in sorted(mentioned - defined):
        findings.append(F("PP-FIG-001", "blocker", "图表清单缺失",
                          "sections/", "正文提到“%s%d”但找不到对应图题" % (kind, n)))
    return findings


def r_fig_nocaption(ctx):
    findings = []
    lines = ctx.all_text.split("\n")
    for i, ln in enumerate(lines):
        if IMG_RE.search(ln):
            near = "\n".join(lines[i:i + 4])
            if not re.search(r"(?:图|表)\s*[0-9一二三四五六七八九十]+[：:．.]", near):
                findings.append(F("PP-FIG-002", "warning", "图片缺少图题/编号",
                                  "sections/", "第 %d 行附近的图片插入没有图题" % (i + 1)))
    return findings[:10]


def r_colloquial(ctx):
    findings = []
    for rel, text in ctx.files.items():
        if not rel.startswith("sections/"):
            continue
        for w in COLLOQUIAL:
            for m in re.finditer(re.escape(w), text):
                findings.append(F("PP-LANG-001", "warning", "口语化表达", rel,
                                  "发现“%s”，建议改为书面学术表达" % w.strip()))
                break
    return findings[:15]


def r_ethics(ctx):
    if not any(w.lower() in ctx.all_text.lower() for w in ETHICS_WORDS):
        return [F("PP-ETH-001", "warning", "伦理/利益冲突声明缺失",
                   "sections/", "全文未提及利益冲突或伦理审查声明，投稿前请按期刊要求补充")]
    return []


RULES = [
    ("PP-ABS-001", "摘要缺失/过短", "blocker", r_absent),
    ("PP-ABS-002", "摘要超长", "warning", r_abstract_long),
    ("PP-KW-001", "关键词缺失", "blocker", r_keywords),
    ("PP-SEC-001", "核心章节缺失", "blocker", r_sections),
    ("PP-CITE-001", "引用格式/幽灵引用", "blocker", r_cite_ghost),
    ("PP-CITE-002", "悬挂文献", "warning", r_cite_dangling),
    ("PP-FIG-001", "图表清单缺失", "blocker", r_fig_missing),
    ("PP-FIG-002", "图片缺图题", "warning", r_fig_nocaption),
    ("PP-LANG-001", "口语化表达", "warning", r_colloquial),
    ("PP-ETH-001", "伦理声明缺失", "warning", r_ethics),
]


def is_paper_dir(d):
    if os.path.isfile(os.path.join(d, "paper.yaml")):
        return True
    return os.path.isdir(os.path.join(d, "sections")) and (
        os.path.isfile(os.path.join(d, "references.bib"))
        or os.path.isfile(os.path.join(d, "references.md")))


def audit(target):
    ctx = Ctx(target)
    findings = []
    for rule_id, title, severity, fn in RULES:
        try:
            findings.extend(fn(ctx) or [])
        except Exception as e:  # 单规则出错不影响整体
            findings.append(F(rule_id, "warning", title + "（规则执行异常）",
                              target, str(e)[:120]))
    summary = {"rules_run": len(RULES),
               "blocker": sum(1 for f in findings if f["severity"] == "blocker"),
               "warning": sum(1 for f in findings if f["severity"] == "warning"),
               "files_checked": len(ctx.files)}
    return {"summary": summary, "findings": findings}


def main():
    ap = argparse.ArgumentParser(description="lhg-paper 投稿前自查审计")
    ap.add_argument("--target", required=True, help="论文目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    args = ap.parse_args()

    if not os.path.isdir(args.target):
        print("目标目录不存在：%s" % args.target, file=sys.stderr)
        return 2

    result = audit(args.target)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("lhg-paper 审计报告：%s" % args.target)
        print("规则 %d 条 | blocker %d | warning %d | 文件 %d" %
              (s["rules_run"], s["blocker"], s["warning"], s["files_checked"]))
        print("-" * 60)
        for f in result["findings"]:
            mark = "⛔" if f["severity"] == "blocker" else "⚠️"
            print("%s [%s][%s] %s\n    %s" %
                  (mark, f["severity"], f["rule_id"], f["title"], f["detail"]))
        if not result["findings"]:
            print("✅ 未发现问题，可以进入人工核查层。")
    return 1 if result["summary"]["blocker"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
