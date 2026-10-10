#!/usr/bin/env python3
"""lhg-poster 渲染前 spec 硬门：渲染类命令触发时校验海报规格。

拦截条件：命令看起来像渲染/导出（render、export、bake、poster 相关），
且项目目录里存在 poster_spec.json / spec.json，但其中有结构性错误
（JSON 非法、占位符残留、文字溢出、对比度不足、字号低于手机端下限）。

行为：
  - 非渲染命令 → 静默放行（exit 0，无输出）
  - 渲染命令 + spec 全合法 → 静默放行
  - 渲染命令 + spec 有结构错误 → deny，输出修复指引
  - 渲染命令 + 找不到 spec → allow + 提醒（不拦截）
  - 环境变量 LHG_POSTER_HOOKS_OFF=1 → 逃生，静默放行
  - 内部出错 → fail-open，静默放行

零第三方依赖。stdin 读 hook payload JSON。
"""

import json
import math
import os
import re
import sys

ESCAPE_ENV = "LHG_POSTER_HOOKS_OFF"
RENDER_HINTS = ("render", "export", "bake", "poster", "screenshot", "png")
SPEC_NAMES = ("poster_spec.json", "spec.json")
PLACEHOLDERS = ("{{", "}}", "TODO", "XXX", "xxx", "[待填]", "待补充", "lorem", "Lorem")
SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__",
             ".claude-plugin", "fixtures"}


def read_stdin_json():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def looks_like_render(command):
    c = (command or "").lower()
    return any(h in c for h in RENDER_HINTS)


def find_spec(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SPEC_NAMES:
                return os.path.join(dirpath, fn)
    return None


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


def contrast(c1, c2):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    if not a or not b:
        return None

    def lum(rgb):
        def ch(v):
            v /= 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, bl = rgb
        return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(bl)

    l1, l2 = lum(a), lum(b)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def check_spec(path):
    """返回 blocker 级错误列表。"""
    errs = []
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except Exception as e:
        return ["spec 不是合法 JSON：%s" % str(e)[:80]]
    canvas = spec.get("canvas", {}) if isinstance(spec, dict) else {}
    w = canvas.get("width", 1080) or 1080
    scale = float(w) / 1080.0
    bg_default = canvas.get("background", "#FFFFFF")
    for e in spec.get("elements", []) or []:
        if not isinstance(e, dict):
            continue
        eid = e.get("id", "?")
        t = str(e.get("text", ""))
        hits = [p for p in PLACEHOLDERS if p in t]
        if hits:
            errs.append("%s：占位符残留 %s，先补真实文案" % (eid, hits[:3]))
        if e.get("type") == "text" and t:
            fs = e.get("font_size", 0) or 0
            bw, bh = e.get("w", 0) or 0, e.get("h", 0) or 0
            if fs and bw and bh:
                lines = max(1, math.ceil(text_width_px(t, fs) / bw))
                if lines * fs * 1.35 > bh * 1.05:
                    errs.append("%s：文字溢出（估算需 %d 行，盒子装不下）" % (eid, lines))
            role = e.get("role", "body")
            if role in ("body", "caption") and fs < 40 * scale:
                errs.append("%s：正文字号 %dpx < 手机端下限 %dpx" %
                            (eid, fs, round(40 * scale)))
            c = contrast(str(e.get("color", "#000000")), str(e.get("bg", bg_default)))
            if c is not None and c < 3.0:
                errs.append("%s：对比度 %.1f:1 < 3.0，手机强光下看不清" % (eid, c))
    return errs


def main():
    if os.environ.get(ESCAPE_ENV) == "1":
        return 0
    try:
        payload = read_stdin_json()
        command = ((payload.get("tool_input") or {}).get("command")) or ""
        if not looks_like_render(command):
            return 0  # 非渲染命令：静默放行

        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        spec = find_spec(root)
        if not spec:
            out = {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason":
                    "lhg-poster：未在项目中找到 poster_spec.json，"
                    "建议先由 renderer 生成锁死的绘制规格再渲染。放行。"}}
            print(json.dumps(out, ensure_ascii=False))
            return 0

        errors = check_spec(spec)
        if errors:
            out = {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    "lhg-poster：spec 有 %d 处结构错误，渲染已拦截：\n- %s\n"
                    "请先修复（或跑 scripts/audit/poster_audit.py 全量校验），"
                    "不要关闭本 hook。如需紧急放行：LHG_POSTER_HOOKS_OFF=1。"
                    % (len(errors), "\n- ".join(errors[:8]))}}
            print(json.dumps(out, ensure_ascii=False))
            return 0
        return 0  # spec 全合法：静默放行
    except Exception:
        return 0  # fail-open


if __name__ == "__main__":
    sys.exit(main())
