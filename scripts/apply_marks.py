# -*- coding: utf-8 -*-
"""apply_marks.py —— 把「重点强调 / 说明卡 / 正文配图」注入 article.json。

设计目标是**可重复执行**：每次从 article.base.json（原始稿）重新生成 article.json，
所以反复跑不会叠加、不会漂移。article.base.json 是唯一事实源，不要手改 article.json。

用法:
    python apply_marks.py --base article.base.json --marks marks.json --out article.json

    # 有配图时必须给 uploaded.json（upload_images.py 的产物）
    python apply_marks.py --base article.base.json --marks marks.json \
        --out article.json --uploaded img/uploaded.json

    # 首次运行：--out 已存在而 --base 不存在时，自动从 --out 复制出基线快照
    # 检查配置是否有效但不写文件
    python apply_marks.py --base article.base.json --marks marks.json --out article.json --dry-run

marks.json 格式（三段都可省略）:
{
  "marks":    [[block下标, "精确子串", "strong|underline|both"], ...],
  "callouts": [[block下标, "卡片标题"], ...],
  "images":   [[block下标, "uploaded.json里的key", "图注"], ...]
}

执行顺序固定为 强调 -> 说明卡 -> 配图，不可调换：
配图会插入新块、改变下标，所以 images 里的下标**一律以 base 的下标为准**，
由脚本在最后一步倒序插入来保证正确。
"""

import argparse
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

MODE_BITS = {"strong": 1, "underline": 2, "both": 3}


def die(msg):
    sys.exit("x " + msg)


def load_json(path, what):
    if not os.path.exists(path):
        die("找不到%s: %s" % (what, path))
    with open(path, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except ValueError as exc:
            die("%s 不是合法 JSON: %s (%s)" % (what, path, exc))


def paragraph_text(block, idx):
    """取出段落纯文本；要求该段落只有单个 run（有强调时须先合并）。"""
    if block.get("type") != "paragraph":
        die("block %d 不是 paragraph（实际 %r），无法加强调" % (idx, block.get("type")))
    runs = block.get("runs")
    if isinstance(runs, str):
        block["runs"] = [{"text": runs}]
        runs = block["runs"]
    if not isinstance(runs, list) or len(runs) != 1:
        n = len(runs) if isinstance(runs, list) else 0
        die("block %d 有 %d 个 run；加强调前需要把该段合并为单个 run" % (idx, n))
    return runs[0]["text"]


def apply_marks(data, marks):
    blocks = data["blocks"]
    grouped = {}
    for item in marks:
        if len(item) != 3:
            die("marks 每项应为 [下标, 子串, 模式]，收到 %r" % (item,))
        idx, sub, mode = item
        if mode not in MODE_BITS:
            die("未知模式 %r（可用: %s）" % (mode, "/".join(MODE_BITS)))
        grouped.setdefault(idx, []).append((sub, mode))

    for idx, items in grouped.items():
        if not isinstance(idx, int) or not 0 <= idx < len(blocks):
            die("block 下标越界: %r（共 %d 块）" % (idx, len(blocks)))
        block = blocks[idx]
        text = paragraph_text(block, idx)
        flags = [0] * len(text)

        for sub, mode in items:
            pos = text.find(sub)
            if pos < 0:
                die("block %d 中找不到子串: %r" % (idx, sub))
            if text.find(sub, pos + 1) >= 0:
                die("block %d 中子串不唯一（出现多次）: %r" % (idx, sub))
            for i in range(pos, pos + len(sub)):
                if flags[i]:
                    die("block %d 中标记区间重叠: %r" % (idx, sub))
                flags[i] |= MODE_BITS[mode]

        merged = []
        for i, ch in enumerate(text):
            if merged and merged[-1]["f"] == flags[i]:
                merged[-1]["text"] += ch
            else:
                merged.append({"text": ch, "f": flags[i]})

        new_runs = []
        for part in merged:
            run = {"text": part["text"]}
            if part["f"] & 1:
                run["strong"] = True
            if part["f"] & 2:
                run["underline"] = True
            new_runs.append(run)

        if "".join(r["text"] for r in new_runs) != text:
            die("block %d 文本被改动（这不该发生）" % idx)
        block["runs"] = new_runs

    return sum(len(v) for v in grouped.values()), len(grouped)


def apply_callouts(data, callouts):
    for item in callouts:
        if len(item) != 2:
            die("callouts 每项应为 [下标, 卡片标题]，收到 %r" % (item,))
        idx, title = item
        block = data["blocks"][idx]
        if block.get("type") != "paragraph":
            die("block %d 不是 paragraph，无法转成说明卡" % idx)
        runs = block.pop("runs")
        block.clear()
        # 文字原样搬运，一个字都不改；卡片只负责视觉分组
        block.update({"type": "callout", "title": title, "paragraphs": [runs]})
    return len(callouts)


def apply_images(data, images, uploaded):
    for item in images:
        if len(item) != 3:
            die("images 每项应为 [下标, key, 图注]，收到 %r" % (item,))
    # 倒序插入，保证前面的下标不被后面插入的块顶偏
    for pos, key, caption in sorted(images, key=lambda x: -x[0]):
        if key not in uploaded:
            die("uploaded.json 里没有图片 key: %r" % key)
        info = uploaded[key]
        data["blocks"].insert(pos + 1, {
            "type": "image",
            "src": info["url"].replace("http://", "https://"),
            "alt": info.get("desc") or key,
            "caption": caption,
        })
    return len(images)


def main():
    ap = argparse.ArgumentParser(description="把强调/说明卡/配图注入 article.json")
    ap.add_argument("--base", required=True, help="原始稿 article.base.json")
    ap.add_argument("--marks", help="配置 marks.json；省略则只做 base->out 的复制")
    ap.add_argument("--out", required=True, help="输出 article.json")
    ap.add_argument("--uploaded", help="upload_images.py 产出的 uploaded.json")
    ap.add_argument("--dry-run", action="store_true", help="只校验配置，不写文件")
    args = ap.parse_args()

    if not os.path.exists(args.base):
        if os.path.exists(args.out):
            if args.dry_run:
                print("[i] (dry-run) 会创建基线快照:", args.base)
            else:
                shutil.copyfile(args.out, args.base)
                print("[OK] 已创建原始基线快照:", args.base)
        else:
            die("--base 与 --out 都不存在，没有可以加工的稿子")

    data = load_json(args.base, "基线稿")
    if not isinstance(data.get("blocks"), list) or not data["blocks"]:
        die("基线稿的 blocks 必须是非空数组")

    cfg = {"marks": [], "callouts": [], "images": []}
    if args.marks:
        loaded = load_json(args.marks, "配置")
        for key in cfg:
            val = loaded.get(key, [])
            if not isinstance(val, list):
                die("%s 必须是数组" % key)
            cfg[key] = val

    if cfg["marks"]:
        n_marks, n_para = apply_marks(data, cfg["marks"])
    else:
        n_marks = n_para = 0

    n_cards = apply_callouts(data, cfg["callouts"]) if cfg["callouts"] else 0

    n_pics = 0
    if cfg["images"]:
        if not args.uploaded:
            die("配置里有 images，但没有给 --uploaded uploaded.json")
        n_pics = apply_images(data, cfg["images"], load_json(args.uploaded, "图片清单"))

    if args.dry_run:
        print("[i] (dry-run) 配置有效：强调 %d 处 / %d 段；说明卡 %d 张；配图 %d 张；"
              "基线块数 %d" % (n_marks, n_para, n_cards, n_pics, len(data["blocks"])))
        return

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print("[OK] %s -> %s" % (args.base, args.out))
    print("     强调 %d 处 / %d 段；说明卡 %d 张；配图 %d 张；总块数 %d"
          % (n_marks, n_para, n_cards, n_pics, len(data["blocks"])))


if __name__ == "__main__":
    main()
