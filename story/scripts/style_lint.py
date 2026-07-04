#!/usr/bin/env python3
"""style_lint — 黑話/壓縮標籤偵測器（reviewer 輔助工具，非自動判官）。

用法：
  python3 style_lint.py --config <adapter>/style_lint_config.json FILE [FILE...]
  python3 style_lint.py --config ... --summary FILE...   # 只出總表
  python3 style_lint.py --config ... --baseline FILE...  # 校準模式：對舊產物量基準線

檢三類：
  1. jargon 詞表命中（管線過程長出的壓縮黑話）
  2. code_patterns 命中（O1/L3/REQ-x/席2/E08 之類設計代號出現在行文）
  3. 疑似新造詞：同檔內重複出現 >=3 次、且不在 whitelist/jargon 的「」引號短語（2–6 字）
     ——這是啟發式，會有誤報，供 reviewer 覆判用。

判讀原則：驗的是「新產物」的行文；舊的已驗收檔案本來就滿是黑話（那是基準線，
不是失敗）。表格欄位與出處引用裡的標籤屬合法引用，命中後由人工覆判。
"""
import argparse, json, re, sys, unicodedata
from collections import Counter
from pathlib import Path


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    return (
        cfg.get("whitelist", []),
        cfg.get("jargon", []),
        [re.compile(p) for p in cfg.get("code_patterns", [])],
    )


QUOTED = re.compile(r"「([^「」]{2,6})」")


def lint_file(path, whitelist, jargon, code_res):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    hits = {"jargon": [], "code": [], "neologism": []}

    for i, line in enumerate(lines, 1):
        for w in jargon:
            if w in line:
                hits["jargon"].append((i, w, line.strip()[:60]))
        for cre in code_res:
            m = cre.search(line)
            if m:
                hits["code"].append((i, m.group(0), line.strip()[:60]))

    counts = Counter(m.group(1) for m in QUOTED.finditer(text))
    known = set(whitelist) | set(jargon)
    for phrase, n in counts.items():
        if n >= 3 and phrase not in known:
            # 過濾純標點/數字/單一常用字重複
            if any(unicodedata.category(c).startswith("L") for c in phrase):
                hits["neologism"].append((phrase, n))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--baseline", action="store_true", help="校準模式：只報數字不報行")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    whitelist, jargon, code_res = load_config(args.config)
    grand = Counter()
    for f in args.files:
        hits = lint_file(f, whitelist, jargon, code_res)
        nj, nc, nn = len(hits["jargon"]), len(hits["code"]), len(hits["neologism"])
        grand.update(jargon_hits=nj, code_hits=nc, neologisms=nn)
        print(f"{f}: 黑話 {nj} 處｜代號 {nc} 處｜疑似新造詞 {nn} 個")
        if not (args.summary or args.baseline):
            for i, w, ctx in hits["jargon"][:20]:
                print(f"    L{i} [{w}] {ctx}")
            for i, w, ctx in hits["code"][:20]:
                print(f"    L{i} <{w}> {ctx}")
            for phrase, n in hits["neologism"]:
                print(f"    疑似新造詞「{phrase}」×{n}")
    print(
        f"TOTAL: 黑話 {grand['jargon_hits']}｜代號 {grand['code_hits']}｜疑似新造詞 {grand['neologisms']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
