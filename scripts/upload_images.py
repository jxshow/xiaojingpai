# -*- coding: utf-8 -*-
"""upload_images.py —— 把配图压到公众号规格并上传，换取正文可引用的 mmbiz 地址。

微信公众号正文里的 <img> 不能直接写外链，必须先用 cgi-bin/media/uploadimg
换成 mmbiz.qpic.cn 的地址，否则不显示。本脚本负责：读清单 -> 压缩 -> 上传 -> 写结果。

用法:
    python upload_images.py --manifest images.json --out img/uploaded.json
    python upload_images.py --manifest images.json --out img/uploaded.json --ready img/ready

images.json 格式（数组；file 支持绝对路径或相对 manifest 所在目录）:
[
  {"key": "vivo_agent", "file": "vivo1.png", "desc": "vivo 开发者大会现场"},
  {"key": "apple_ctx",  "file": "apple_ctx.jpg", "desc": "Apple 官方：Siri AI 个人上下文"}
]

输出 uploaded.json:
{ "vivo_agent": {"url": "https://mmbiz.qpic.cn/...", "desc": "..."}, ... }

依赖 Pillow（venv 解释器）：
    C:\\Users\\xhshow\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

sys.stdout.reconfigure(encoding="utf-8")

API_TOKEN = "https://api.weixin.qq.com/cgi-bin/token"
API_STABLE_TOKEN = "https://api.weixin.qq.com/cgi-bin/stable_token"
API_UPLOADIMG = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
UA = "Mozilla/5.0 (xiaojingpai)"
LIMIT = 1000 * 1000  # uploadimg 上限 1MB

# 凭据查找顺序：环境变量 > WECHAT_ENV_FILE > 用户级凭据目录 > 旧工作区
ENV_CANDIDATES = [
    os.environ.get("WECHAT_ENV_FILE", ""),
    os.path.join(os.path.expanduser("~"), ".workbuddy", "wechat", ".env"),
    r"D:\AI编程\2026-09-07-21-44-19\.env",
]


def creds():
    env = {}
    for path in ENV_CANDIDATES:
        if path and os.path.exists(path):
            for raw in open(path, encoding="utf-8"):
                raw = raw.strip()
                if raw and not raw.startswith("#") and "=" in raw:
                    k, v = raw.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    appid = os.environ.get("WECHAT_APPID") or env.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_APPSECRET") or env.get("WECHAT_APPSECRET")
    if not appid or not secret:
        sys.exit("x 找不到凭据。请确认 %s 存在且含 WECHAT_APPID / WECHAT_APPSECRET"
                 % ENV_CANDIDATES[1])
    return appid, secret


def post_json(url, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": UA},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_token(appid, secret, cache_path):
    if os.path.exists(cache_path):
        try:
            data = json.load(open(cache_path, encoding="utf-8"))
            if data.get("appid") == appid and data.get("expires_at", 0) > time.time() + 300:
                return data["access_token"]
        except Exception:
            pass
    # stable_token 并发安全，不会被别处刷新顶掉
    data = post_json(API_STABLE_TOKEN, {
        "grant_type": "client_credential", "appid": appid, "secret": secret,
    })
    if "access_token" not in data:
        qs = urllib.parse.urlencode({"grant_type": "client_credential",
                                     "appid": appid, "secret": secret})
        with urllib.request.urlopen(API_TOKEN + "?" + qs, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        sys.exit("x 获取 access_token 失败: %s\n"
                 "  常见原因: IP 不在公众号后台白名单 / AppID 或 AppSecret 不对。" % data)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump({"appid": appid, "access_token": data["access_token"],
                   "expires_at": time.time() + int(data.get("expires_in", 7200))}, fh)
    return data["access_token"]


def prepare(name, src, ready_dir):
    """转 JPEG 并逐档降质缩放到 1MB 以内。"""
    from PIL import Image  # 延迟导入，便于 --help 在无 Pillow 时也能用
    os.makedirs(ready_dir, exist_ok=True)
    out = os.path.join(ready_dir, name + ".jpg")
    with Image.open(src) as im:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        for max_w in (1600, 1400, 1200, 1000):
            for quality in (90, 84, 78, 72):
                copy = im.copy()
                if copy.width > max_w:
                    ratio = max_w / float(copy.width)
                    copy = copy.resize((max_w, int(copy.height * ratio)), Image.LANCZOS)
                buf = io.BytesIO()
                copy.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
                blob = buf.getvalue()
                if len(blob) <= LIMIT:
                    with open(out, "wb") as fh:
                        fh.write(blob)
                    return out, len(blob), copy.size
    sys.exit("x 无法压到 1MB 以内: %s（试试先手动裁掉白边）" % name)


def upload(tok, path):
    boundary = "----WXImg" + uuid.uuid4().hex
    with open(path, "rb") as fh:
        blob = fh.read()
    name = os.path.basename(path)
    body = b"".join([
        ("--%s\r\n" % boundary).encode(),
        ('Content-Disposition: form-data; name="media"; filename="%s"\r\n' % name).encode(),
        b"Content-Type: image/jpeg\r\n\r\n",
        blob, b"\r\n",
        ("--%s--\r\n" % boundary).encode(),
    ])
    req = urllib.request.Request(
        API_UPLOADIMG + "?access_token=" + tok, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary, "User-Agent": UA},
        method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="压缩并上传配图到微信，换取正文可引用地址")
    ap.add_argument("--manifest", required=True, help="图片清单 images.json")
    ap.add_argument("--out", required=True, help="输出 uploaded.json")
    ap.add_argument("--ready", help="压缩后文件的存放目录（默认 <out同级>/ready）")
    args = ap.parse_args()

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    if not isinstance(manifest, list) or not manifest:
        sys.exit("x 清单必须是非空数组")
    manifest_dir = os.path.dirname(os.path.abspath(args.manifest))
    ready_dir = args.ready or os.path.join(os.path.dirname(os.path.abspath(args.out)), "ready")

    appid, secret = creds()
    cache_path = os.path.join(os.path.dirname(os.path.abspath(args.out)), ".wechat_token_cache.json")
    tok = get_token(appid, secret, cache_path)
    print("[OK] access_token 就绪")

    result = {}
    if os.path.exists(args.out):
        try:  # 保留历史结果，便于增量重传
            old = json.load(open(args.out, encoding="utf-8"))
            if isinstance(old, dict):
                result.update(old)
        except Exception:
            pass

    for item in manifest:
        key = item.get("key")
        src = item.get("file")
        if not key or not src:
            sys.exit("x 清单项缺少 key/file: %r" % (item,))
        if not os.path.isabs(src):
            src = os.path.join(manifest_dir, src)
        if not os.path.exists(src):
            print("x %-12s 源文件不存在: %s" % (key, src))
            continue
        path, size, dim = prepare(key, src, ready_dir)
        res = upload(tok, path)
        if "url" not in res:
            print("x %-12s 上传失败: %s" % (key, res))
            continue
        result[key] = {"url": res["url"], "desc": item.get("desc") or key}
        print("[OK] %-12s %7d B  %-11s -> %s"
              % (key, size, "%dx%d" % dim, res["url"]))

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print("\n已写入 %s（%d 张）" % (args.out, len(result)))


if __name__ == "__main__":
    main()
