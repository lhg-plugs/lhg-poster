#!/usr/bin/env python3
"""lhg-poster 确定性海报审计：15 条规则，零第三方依赖。

扫描目录中的 poster_spec.json（海报绘制规格），检查文字溢出、
安全边距、手机端字号下限、对比度、占位符残留等；输出 JSON 与
人类可读报告；有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 poster_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

spec.json 格式（由 renderer agent 按 lhg-poster-render 规范生成）：
    {"canvas": {"width":1080,"height":1920,"background":"#FFFFFF"},
     "brand": "品牌名",
     "palette": ["#111111", ...],
     "info": {"title":"..","date_time":"..","contact":".."},
     "elements": [{"id":"title","type":"text","role":"title",
                   "x":80,"y":120,"w":920,"h":200,"text":"..",
                   "font_size":84,"color":"#111111","bg":"#FFFFFF","layer":2},
                  {"id":"bg","type":"image","x":0,"y":0,"w":1080,"h":1920,
                   "source":"ai-bg.png","layer":0}]}

规则文案均为本项目原创（"规格锁死+校验清单"的方法论思路受
bianbianzhu/curriculum 的 ai-news-poster skill 启发，其许可未核实，
仅借鉴高层思路，未复制任何第三方原文；详见仓库 ATTRIBUTION.md）。
"""

import argparse
import json
import math
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-poster/poster-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}
SPEC_NAMES = ("poster_spec.json", "spec.json")
PLACEHOLDERS = ("{{", "}}", "TODO", "XXX", "xxx", "[待填]", "待补充", "lorem", "Lorem")
BASE_WIDTH = 1080.0  # 字号基准画布宽度


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {"rule_id": self.rule_id, "severity": self.severity,
                "category": self.category, "title": self.title,
                "file": self.file, "line": self.line,
                "snippet": self.snippet, "detail": self.detail}


def is_cjk(ch):
    o = ord(ch)
    return (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or
            0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF)


def text_width_px(text, font_size):
    return sum(font_size * (1.0 if is_cjk(c) else 0.55) for c in text)


def hex_to_rgb(s):
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return None
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def luminance(rgb):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(c1, c2):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    if not a or not b:
        return None
    l1, l2 = luminance(a), luminance(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def find_spec(target):
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SPEC_NAMES:
                return os.path.join(dirpath, fn)
    return None


class Ctx:
    def __init__(self, target):
        self.target = target
        self.findings = []
        self.spec_path = find_spec(target)
        self.spec = None
        self.spec_error = None
        if self.spec_path:
            try:
                with open(self.spec_path, encoding="utf-8") as fh:
                    self.spec = json.load(fh)
            except Exception as e:
                self.spec_error = str(e)[:120]
        self.rel = os.path.relpath(self.spec_path, target) if self.spec_path else "(无 spec)"

    def add(self, rule_id, severity, category, title, snippet="", detail=""):
        self.findings.append(Finding(rule_id, severity, category, title,
                                     self.rel, 0, snippet, detail))

    def canvas(self):
        return (self.spec or {}).get("canvas", {}) if self.spec else {}

    def elements(self):
        els = (self.spec or {}).get("elements", []) if self.spec else []
        return [e for e in els if isinstance(e, dict)]

    def scale(self):
        w = self.canvas().get("width", BASE_WIDTH) or BASE_WIDTH
        try:
            return float(w) / BASE_WIDTH
        except (TypeError, ValueError):
            return 1.0


# ---------------- 规格规则 ----------------

def rule_spec_json(ctx):
    if not ctx.spec_path:
        ctx.add("PST-SPEC-001", "blocker", "spec", "找不到 poster_spec.json",
                "", "目录中没有 poster_spec.json / spec.json，先由 renderer 生成")
    elif ctx.spec_error:
        ctx.add("PST-SPEC-001", "blocker", "spec", "spec 不是合法 JSON",
                "", "解析失败：%s" % ctx.spec_error)


def rule_spec_canvas(ctx):
    if not ctx.spec:
        return
    c = ctx.canvas()
    w, h = c.get("width"), c.get("height")
    if not isinstance(w, (int, float)) or not isinstance(h, (int, float)) or w <= 0 or h <= 0:
        ctx.add("PST-SPEC-002", "blocker", "spec", "canvas 尺寸非法",
                "", "width/height 必须为正数，当前：%s x %s" % (w, h))


def rule_spec_elements(ctx):
    if not ctx.spec:
        return
    if not ctx.elements():
        ctx.add("PST-SPEC-003", "warning", "spec", "elements 为空",
                "", "规格中没有任何元素，海报是白板")


# ---------------- 文字规则 ----------------

def rule_text_overflow(ctx):
    for e in ctx.elements():
        if e.get("type") != "text" or not e.get("text"):
            continue
        fs = e.get("font_size", 0) or 0
        w, h = e.get("w", 0) or 0, e.get("h", 0) or 0
        if fs <= 0 or w <= 0 or h <= 0:
            continue
        tw = text_width_px(str(e["text"]), fs)
        lines = max(1, math.ceil(tw / w))
        need_h = lines * fs * 1.35
        if need_h > h * 1.05:
            ctx.add("PST-TEXT-001", "blocker", "text",
                    "文字溢出：%s" % e.get("id", "?"),
                    str(e["text"])[:40],
                    "估算需 %d 行、高 %.0fpx，盒子仅 %d 行、高 %dpx（字号 %d）" %
                    (lines, need_h, max(1, int(h / (fs * 1.35))), h, fs))


def rule_text_placeholder(ctx):
    for e in ctx.elements():
        t = str(e.get("text", ""))
        hits = [p for p in PLACEHOLDERS if p in t]
        if hits:
            ctx.add("PST-TEXT-002", "blocker", "text",
                    "占位符残留：%s" % e.get("id", "?"),
                    t[:40], "含占位符 %s，先补真实文案再绘制" % hits[:3])


def rule_text_title_length(ctx):
    for e in ctx.elements():
        if e.get("type") == "text" and e.get("role") == "title":
            t = str(e.get("text", ""))
            if len(t) > 14:
                ctx.add("PST-TEXT-003", "warning", "text",
                        "标题过长（%d 字）：%s" % (len(t), e.get("id", "?")),
                        t[:40], "手机端标题建议 ≤14 字，超长请拆成主副标题")


# ---------------- 版式规则 ----------------

def rule_margin(ctx):
    c = ctx.canvas()
    w = c.get("width") or 0
    if w <= 0:
        return
    safe = w * 0.04
    for e in ctx.elements():
        if e.get("type") != "text":
            continue
        x, y = e.get("x", 0) or 0, e.get("y", 0) or 0
        ew, eh = e.get("w", 0) or 0, e.get("h", 0) or 0
        bad = []
        if x < safe:
            bad.append("左 %.0fpx" % x)
        if y < safe:
            bad.append("上 %.0fpx" % y)
        if w - (x + ew) < safe:
            bad.append("右 %.0fpx" % (w - (x + ew)))
        ch = c.get("height") or 0
        if ch and ch - (y + eh) < safe:
            bad.append("下 %.0fpx" % (ch - (y + eh)))
        if bad:
            ctx.add("PST-MARGIN-001", "warning", "layout",
                    "安全边距不足：%s" % e.get("id", "?"),
                    "", "以下边距 < 4%% 画布宽（%.0fpx）：%s" % (safe, "、".join(bad)))


def rule_font_min(ctx):
    s = ctx.scale()
    for e in ctx.elements():
        if e.get("type") != "text":
            continue
        fs = e.get("font_size", 0) or 0
        role = e.get("role", "body")
        if role in ("body", "caption") and fs < 40 * s:
            ctx.add("PST-FONT-001", "blocker", "readability",
                    "正文字号过小：%s" % e.get("id", "?"),
                    "", "字号 %dpx < 手机端下限 %dpx（以 %d 宽画布计），手机上看不清" %
                    (fs, round(40 * s), round(BASE_WIDTH * s)))
        elif role == "title" and fs < 72 * s:
            ctx.add("PST-FONT-001", "warning", "readability",
                    "标题字号偏小：%s" % e.get("id", "?"),
                    "", "标题字号 %dpx < 建议 %dpx，手机端冲击力不足" % (fs, round(72 * s)))


def rule_font_hierarchy(ctx):
    titles = [e.get("font_size", 0) or 0 for e in ctx.elements()
              if e.get("type") == "text" and e.get("role") == "title"]
    bodies = [e.get("font_size", 0) or 0 for e in ctx.elements()
              if e.get("type") == "text" and e.get("role") in ("body", "caption")]
    if titles and bodies and max(titles) < max(bodies) * 1.4:
        ctx.add("PST-FONT-002", "warning", "readability", "字号层级不分明",
                "", "最大标题 %dpx < 最大正文 %dpx × 1.4，标题压不住版面" %
                (max(titles), max(bodies)))


def rule_contrast(ctx):
    bg_default = ctx.canvas().get("background", "#FFFFFF")
    for e in ctx.elements():
        if e.get("type") != "text":
            continue
        c = contrast(str(e.get("color", "#000000")), str(e.get("bg", bg_default)))
        if c is None:
            continue
        if c < 3.0:
            ctx.add("PST-CONTRAST-001", "blocker", "readability",
                    "对比度不足：%s" % e.get("id", "?"),
                    "", "文字 %s / 背景 %s 对比度 %.1f:1 < 3.0，手机强光下看不清" %
                    (e.get("color"), e.get("bg", bg_default), c))


def rule_color_count(ctx):
    if not ctx.spec:
        return
    colors = set()
    for c in (ctx.spec.get("palette") or []):
        colors.add(str(c).lower())
    for e in ctx.elements():
        for k in ("color", "bg"):
            if e.get(k):
                colors.add(str(e[k]).lower())
    if len(colors) > 5:
        ctx.add("PST-COLOR-001", "warning", "layout", "配色过多（%d 种）" % len(colors),
                "", "建议 ≤5 种颜色（含黑白），小白海报颜色越多越乱")


# ---------------- 信息完整性规则 ----------------

def rule_info(ctx):
    if not ctx.spec:
        return
    info = ctx.spec.get("info", {}) or {}
    keys = {"title": "标题", "date_time": "时间", "contact": "联系方式"}
    missing = [v for k, v in keys.items() if not info.get(k)]
    if len(missing) >= 2:
        ctx.add("PST-INFO-001", "warning", "info", "必备信息缺失过多",
                "", "缺：%s。标题/时间/联系方式至少要有两项是确定的" % "、".join(missing))


def rule_brand(ctx):
    if not ctx.spec:
        return
    brand = str(ctx.spec.get("brand", "") or "")
    if not brand:
        return
    texts = " ".join(str(e.get("text", "")) for e in ctx.elements())
    if brand not in texts:
        ctx.add("PST-BRAND-001", "warning", "info", "品牌名未出现在海报文字中",
                "", "brand 为“%s”，但所有文字元素里都没出现，遮住 logo 就认不出是谁家" % brand)


def rule_overlap(ctx):
    texts = [e for e in ctx.elements() if e.get("type") == "text"]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            ax, ay, aw, ah = (a.get("x", 0) or 0, a.get("y", 0) or 0,
                              a.get("w", 0) or 0, a.get("h", 0) or 0)
            bx, by, bw, bh = (b.get("x", 0) or 0, b.get("y", 0) or 0,
                              b.get("w", 0) or 0, b.get("h", 0) or 0)
            ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
            iy = max(0, min(ay + ah, by + bh) - max(ay, by))
            if ix * iy == 0:
                continue
            small = min(aw * ah, bw * bh)
            if small > 0 and ix * iy / small > 0.3:
                ctx.add("PST-OVERLAP-001", "warning", "layout",
                        "文字元素重叠：%s × %s" % (a.get("id", "?"), b.get("id", "?")),
                        "", "重叠面积超小盒 30%，手机端会糊成一团")


def rule_image_source(ctx):
    for e in ctx.elements():
        if e.get("type") == "image" and not e.get("source"):
            ctx.add("PST-IMG-001", "nit", "info", "图片元素缺来源标注：%s" % e.get("id", "?"),
                    "", "建议标注图片来源（自制/AI 生成/已购版权），避免版权纠纷")


RULES = [
    ("PST-SPEC-001", rule_spec_json), ("PST-SPEC-002", rule_spec_canvas),
    ("PST-SPEC-003", rule_spec_elements),
    ("PST-TEXT-001", rule_text_overflow), ("PST-TEXT-002", rule_text_placeholder),
    ("PST-TEXT-003", rule_text_title_length),
    ("PST-MARGIN-001", rule_margin),
    ("PST-FONT-001", rule_font_min), ("PST-FONT-002", rule_font_hierarchy),
    ("PST-CONTRAST-001", rule_contrast), ("PST-COLOR-001", rule_color_count),
    ("PST-INFO-001", rule_info), ("PST-BRAND-001", rule_brand),
    ("PST-OVERLAP-001", rule_overlap), ("PST-IMG-001", rule_image_source),
]

SEV_ORDER = {"blocker": 0, "warning": 1, "nit": 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args()

    if not os.path.isdir(args.target):
        print("target 不是目录：%s" % args.target, file=sys.stderr)
        return 2

    ctx = Ctx(args.target)
    for _rid, fn in RULES:
        try:
            fn(ctx)
        except Exception as e:
            ctx.add("PST-INT-001", "nit", "internal", "规则执行异常",
                    "", "%s: %s" % (fn.__name__, str(e)[:80]))

    ctx.findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.rule_id))
    summary = {"tool": TOOL, "version": VERSION, "target": args.target,
               "rules_run": len(RULES),
               "blocker": sum(1 for f in ctx.findings if f.severity == "blocker"),
               "warning": sum(1 for f in ctx.findings if f.severity == "warning"),
               "nit": sum(1 for f in ctx.findings if f.severity == "nit")}
    out = {"summary": summary,
           "findings": [f.to_dict() for f in ctx.findings]}

    if args.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("lhg-poster 审计报告（%d 条规则）" % len(RULES))
        print("目标：%s" % args.target)
        print("blocker=%d warning=%d nit=%d" % (
            summary["blocker"], summary["warning"], summary["nit"]))
        for f in ctx.findings:
            print("[%s] %s %s (%s)" % (f.severity.upper(), f.rule_id, f.title, f.file or "-"))
            if f.detail:
                print("    %s" % f.detail)

    worst = min([SEV_ORDER[f.severity] for f in ctx.findings], default=99)
    threshold = SEV_ORDER[args.fail_on]
    return 2 if worst <= threshold else 0


if __name__ == "__main__":
    sys.exit(main())
