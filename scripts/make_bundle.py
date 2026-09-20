# -*- coding: utf-8 -*-
"""make_bundle.py —— 把整条「小鲸排 Skill」链路打包成一个可搬运的 zip。

换电脑时，这个 zip 解开 + 复制凭据 = 完整环境，不需要重新摸索。

用法:
    python make_bundle.py                              # 默认输出到 ~/.workbuddy/bundles/
    python make_bundle.py --out "D:/小鲸排.zip"
    python make_bundle.py --with-env                   # ⚠️ 连凭据一起打包（含明文密钥）

打包内容:
    skills/xiaojingpai          总控 SOP + 通用脚本（本 skill，含合规校验器）
    skills/xiaojingpai-render   排版引擎（4 套主题 + 渲染器）
    skills/xiaojingpai-push     官方 API 推送 + 封面生成
    README.md / 口令卡.md        用法与口令
    install.md                  新机器安装步骤

默认**不含** .env —— 明文密钥不该随手进网盘。需要时显式 --with-env。
"""

import argparse
import os
import shutil
import sys
import zipfile
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

HOME = os.path.expanduser("~")
SKILLS_DIR = os.path.join(HOME, ".workbuddy", "skills")
ENV_PATH = os.path.join(HOME, ".workbuddy", "wechat", ".env")

BUNDLE_SKILLS = [
    "xiaojingpai",          # 总控 + 合规校验（必须）
    "xiaojingpai-render",   # 排版（必须）
    "xiaojingpai-push",     # 推送（必须）
]

# 不打包的目录/文件
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache"}
SKIP_FILES = {".wechat_token_cache.json", ".wechat_push_state.json", ".DS_Store"}


def should_skip(rel):
    parts = rel.split(os.sep)
    if any(p in SKIP_DIRS for p in parts):
        return True
    return os.path.basename(rel) in SKIP_FILES


def main():
    ap = argparse.ArgumentParser(description="打包整条公众号发布链路")
    ap.add_argument("--out", help="输出 zip 路径")
    ap.add_argument("--with-env", action="store_true",
                    help="把凭据 .env 一并打包（含明文密钥，谨慎使用）")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d")
    out = args.out or os.path.join(HOME, ".workbuddy", "bundles",
                                   "xiaojingpai-%s.zip" % stamp)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    missing = [s for s in BUNDLE_SKILLS if not os.path.isdir(os.path.join(SKILLS_DIR, s))]
    if missing:
        sys.exit("x 缺少 skill 目录，无法打包: %s\n  期望位置: %s"
                 % (", ".join(missing), SKILLS_DIR))

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for skill in BUNDLE_SKILLS:
            root = os.path.join(SKILLS_DIR, skill)
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if fn in SKIP_FILES:
                        continue
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, SKILLS_DIR)
                    if should_skip(rel):
                        continue
                    zf.write(full, os.path.join("skills", rel))
                    count += 1

        # 说明文件
        for doc in ("README.md", "口令卡.md"):
            src = os.path.join(SKILLS_DIR, "xiaojingpai", "references", doc)
            if os.path.exists(src):
                zf.write(src, doc)
        install = os.path.join(SKILLS_DIR, "xiaojingpai", "references", "new-machine-setup.md")
        if os.path.exists(install):
            zf.write(install, "install.md")

        if args.with_env:
            if not os.path.exists(ENV_PATH):
                sys.exit("x --with-env 指定了但找不到凭据文件: %s" % ENV_PATH)
            zf.write(ENV_PATH, "wechat/.env")
            print("[!] 已包含凭据 .env —— 这个 zip 含明文密钥，别放公开网盘。")

    size = os.path.getsize(out)
    print("[OK] 打包完成: %s" % out)
    print("     %d 个文件, %.1f KB" % (count, size / 1024.0))
    print("     含 skill: %s" % ", ".join(BUNDLE_SKILLS))
    print("     凭据: %s" % ("已包含（注意保管）" if args.with_env else "未包含（需另行复制）"))


if __name__ == "__main__":
    main()
