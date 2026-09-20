---
name: jingxuan-publish-flow
description: 鲸选AI 公众号「排版 → 配图 → 重点标注 → 推送草稿箱」全流程总控。把腾讯文档/Word/Markdown 变成可发布的公众号文章并写进草稿箱。当用户说「排版并推送到公众号」「把这篇推到草稿箱」「排这篇推草稿箱」「用AGI绿排版这篇」「配图 + 重点标粗下划线」「一键发布」「整理并推草稿」，或同时给出文章链接 + 公众号/草稿箱/草稿/鲸选AI 字样时使用。用户只说中文即可，不需要说出任何 skill 名。本文是入口 SOP，具体排版规则读 jingxuan-ai-gzh，推送细节读 jingxuan-draft-push。禁止用浏览器扫码登录 mp.weixin.qq.com。
agent_created: true
---

# 鲸选AI 公众号发布流水线（总控）

这是**入口**。收到任务先读本文确定顺序，再按需读另外两个 skill：

| 需要 | 读 |
|---|---|
| 主题配方、article.json 字段、渲染器 | skill `jingxuan-ai-gzh`（+ 其 `references/theme-index.md`、`input-and-ir.md`） |
| 草稿接口、封面、图片上传、token 坑 | skill `jingxuan-draft-push`（+ 其 `references/pipeline-notes.md`） |
| 用户视角的说法与默认值 | 本 skill 的 `references/口令卡.md` |
| 换电脑 | 本 skill 的 `references/new-machine-setup.md` |

**绝对不要**为了推送驱动浏览器登录 `mp.weixin.qq.com`。凭据在本机，草稿箱是 `cgi-bin/draft/add` 一个接口的事。这条是硬约束（用户曾多次被逼扫码，明确表达过不满）。

## 环境准备（每个 shell 会话都要）

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"   # Git Bash 否则 dirname/cd 报错
export PYTHONIOENCODING=utf-8                            # 中文不乱码
PY="C:/Users/xhshow/.workbuddy/binaries/python/versions/3.13.12/python.exe"
VP="C:/Users/xhshow/.workbuddy/binaries/python/envs/default/Scripts/python.exe"   # 带 Pillow，封面/配图用
FLOW="C:/Users/xhshow/.workbuddy/skills/jingxuan-publish-flow/scripts"
JX="C:/Users/xhshow/.workbuddy/skills/jingxuan-ai-gzh"
PUSH="C:/Users/xhshow/.workbuddy/skills/jingxuan-draft-push/scripts"
```

路径一律写 `C:/...`，**不要** `/c/...`（会被拼成 `d:\c\...`）。Bash 里用 `C:/...` 传给 Windows 程序没问题。

**工作目录约定**：每篇文章一个独立目录，建议 `D:\AI编程\<当前日期>\<短名>-<主题>\`。
产物固定为 `article.base.json`（原始稿，唯一事实源）/ `article.json`（加工后）/ `build/`（渲染输出）/ `img/`（配图）。

## 主流程（8 步）

### ① 取原文（含加粗信息）

腾讯文档两步走，缺一不可：

- `mcp__tencent-docs__get_content`（`file_id` 或完整链接）→ 拿到正文与结构
- `mcp__tencent-docs__manage.export_file` + `export_progress` → 拿 docx 下载地址，
  `curl` 下来后解压 `word/document.xml` 逐 run 读 `<w:b/>`，**确认原文到底哪里加粗**

只做第一步会丢加粗信息，导致「自行编造重点」。把解析结果存成 JSON 备用。

> 腾讯文档导出是签名 URL，约 30 分钟过期；过期就重新调 `export_file`。

### ② 写 article.base.json

按 `jingxuan-ai-gzh/references/input-and-ir.md` 的字段规范。要点：

- `theme` 填主题 ID（见下表）
- 每段 `runs` **先合并成单个 run**，强调交给第 ⑤ 步统一打，避免多 run 文本错位
- 文字零改动：不改错别字（发现就报告用户，不擅自改）、不补小标题、不删内容
- 加粗**忠实映射**：原文局部加粗的短词 → 留给第 ⑤ 步；原文整句加粗 → `strong`

推荐用脚本从解析结果直接生成，而不是手打 JSON，避免文字误差。

### ③ 渲染

```bash
node "$JX/scripts/render_article.mjs" "<文章目录>/article.json" --out "<文章目录>/build"
```

⚠️ **渲染器不覆盖已存在的输出目录**，重渲染前先 `rm -rf build && mkdir build`。

产出 `article.html`（品牌渐变版）/ `article-compatible.html`（纯色稳妥版）/ `preview.html` / `article.txt` / `report.json`。

### ④ 合规校验（推送前必做）

```bash
"$PY" "C:/Users/xhshow/.workbuddy/skills/gzh-design-skill/scripts/validate_gzh_html.py" \
      "<文章目录>/build/article.html"
```

有 ERROR 先修 HTML，别往下走。

### ⑤ 重点标注 + 说明卡 + 配图

配置写成 `marks.json`，用脚本注入（**可重复执行**，每次从 base 重算，不叠加）：

```bash
"$PY" "$FLOW/apply_marks.py" \
    --base "<文章目录>/article.base.json" \
    --marks "<文章目录>/marks.json" \
    --out "<文章目录>/article.json" \
    --uploaded "<文章目录>/img/uploaded.json"
```

`marks.json`：

```json
{
  "marks":    [[block下标, "精确子串", "strong|underline|both"]],
  "callouts": [[block下标, "卡片标题"]],
  "images":   [[block下标, "uploaded里的key", "图注"]]
}
```

脚本会强制校验：子串必须存在且唯一、区间不重叠、文本零改动，任何一条不满足就报错退出（宁可不做，不做错）。
**`images` 的下标一律以 base 为准**，脚本内部最后倒序插入，顺序不能调换。

#### 用户说「你看着标重点」时的判断准则

- **`strong`（整句黑粗）** 给**结论句 / 定义句 / 转折后的判断**——能独立成立的一句观点。
- **`underline`（2px 主题色下划线）** 给**概念词、专有名词、产品名、关键机制**——通常 2~6 个字。
- **`both`** 只给全文最核心的 1~3 个概念，别滥用。
- 密度：整篇 `marks` 数量控制在**段落数的 1/3 左右**，同一段最多 1~2 处。
- **原文本来就有加粗的，优先标它**；其余靠自己判断。
- 不因为「要展示渐变/下划线」而造重点。原文没有可映射的强调时，就少标或不标。

#### 说明卡（callout）

把**并列罗列、清单式、时间线式**的整段包成浅绿卡片，视觉上跳出来。
卡片标题是**事实性标签**（如「发布节奏」），不编造评价。文字原样搬运，一个字不改。
AGI绿 的 callout 样式：底 `#f5faf6` + 边 `1px solid #cfe7d5` + 10px 圆角 + 黑粗题 + 灰字正文。

#### 配图

见下节。

### ⑥ 配图上传

正文图片**必须先上传换 mmbiz 地址**，写外链不显示。清单写成 `img/images.json`：

```json
[{"key": "apple_ctx", "file": "apple_ctx.jpg", "desc": "Apple 官方：Siri AI 个人上下文"}]
```

```bash
"$VP" "$FLOW/upload_images.py" \
    --manifest "<文章目录>/img/images.json" \
    --out "<文章目录>/img/uploaded.json"
```

然后回到第 ⑤ 步把 `images` 写进 `marks.json`，重跑 `apply_marks.py`，再重渲染（第 ③ 步）。

**取图原则**：

- 优先**官方新闻稿**：Apple `apple.com/newsroom/images/...` 可直接抓且可用；品牌官网新闻中心次之。
- **JS 渲染页面抓不到正文图**（腾讯新闻、OPPO 官网都踩过）。抓不到就**如实告诉用户**，别用劣质图凑。
- 分辨率太小的（如 200×200 缩略图）不要用。
- **图注必须标图源**，如「（图源：Apple 官方新闻稿）」。
- 版权风险：只用官方素材，不抓未知来源的图。

### ⑦ 封面 + 推送

```bash
# 封面（草稿接口强制要封面，缺了报 40007）
"$VP" "$PUSH/make_cover.py" "文章标题" "鲸选AI · AGI绿" "<目录>/cover.png" --color "#2ea250"

# 连通性自检（不写草稿）
"$PY" "$PUSH/push_to_wechat_draft.py" --check

# 新建草稿
"$PY" "$PUSH/push_to_wechat_draft.py" "<目录>/build/article.html" --html \
    --title "标题" --author "鲸选AI" --cover "<目录>/cover.png"

# 更新已有草稿（复用原封面，避免素材库重复）
"$PY" "$PUSH/push_to_wechat_draft.py" "<目录>/build/article.html" --html \
    --title "标题" --author "鲸选AI" \
    --thumb-media-id "<封面media_id>" --media-id "<草稿media_id>"
```

### ⑧ 回读验证（不能省）

推送后用 `cgi-bin/draft/get` 拉回内容，核对 `<img>` 数 / `border-bottom` 数 / `font-weight:700` 数 /
`font-size:48px` 数 / `span leaf` 数是否与本地一致——确认微信没吞样式。

## ⚠️ 覆盖保护（最容易出事的地方）

**`draft/update` 是整篇替换，不是增量合并。** 用户只要在公众号后台手工改过那篇，
我推一次就全没了。

规则：

1. **用户在后台动过的稿子，绝不再带 `--media-id` 推。**
2. 不确定时先 `draft/get`（只读）拉回来看看，或直接问用户。
3. 脚本内置指纹保护：内容不一致会**拒绝更新并退出**；要用 `--force` 才覆盖。
4. 想保留后台那份 → **去掉 `--media-id`，用 `draft/add` 新建一条**。
5. 本地 JSON 是唯一事实源，**后台的改动永远不会回流到本地**。两边分叉必丢一边。

## 主题选择

| ID | 名称 | 适合 | 辨识 |
|---|---|---|---|
| agi-green | 鲸选AGI绿 | **默认**。新闻解读、行业观察、叙事长文 | 白底 + 栈式 48px 绿编号 + 可选 10px 灰英文标签 + 20px 黑粗标题 |
| byte-green | 鲸选字节绿 | 工具实测、教程、功能清单 | 渐变标题 + 渐变绿签 |
| magazine-green | 鲸选杂志绿 | 测评、快讯、工具盘点 | 杂志封面 + 导读卡 + 「01 标题」 |
| pro-blue | 鲸选Pro蓝 | 商业观察、专业长文 | 蓝色数字徽章 + 居中斜体蓝标题 |

- 绿主题主色统一 `#2ea250 → #09fc3c`；AGI绿封面色用 `#2ea250`。
- **一篇只用一个主主题**，不能按段混用。
- 用户没指定主题：新闻/行业长文用 AGI绿，工具实测/教程用字节绿，不提问直接做。

## runs 强调类型（渲染器已支持）

| 字段 | 效果 | 用途 |
|---|---|---|
| `strong` | 黑色加粗（`font-weight:700`） | 整句重点 |
| `mark` | 渐变绿字色，**无底线** | 需要渐变视觉的重点词 |
| `underline` | 2px 主题色下划线，**可与 strong 叠加** | 短关键词 |

H3 的黑粗字自带 2px 绿底线，不要额外加 `underline`。

## 固定默认值

| 项 | 值 |
|---|---|
| 公众号 | 鲸选AI |
| 作者字段 | `鲸选AI`（接口上限 8 字；标题上限 64 字） |
| 凭据 | `C:\Users\xhshow\.workbuddy\wechat\.env`（`WECHAT_APPID` / `WECHAT_APPSECRET`） |
| 封面尺寸 | 900×383 |

## 交付时要说清

- 主题选择、块数/字数/强调处数、配图张数与来源
- `report.json` 里的阻塞项与警告
- 没做到的事：抓不到的图、疑似笔误（**报告但不改**）
- 草稿 media_id，以及是新建还是更新

## 脚本索引

| 脚本 | 作用 |
|---|---|
| `scripts/apply_marks.py` | 强调 / 说明卡 / 配图注入 article.json（可重复执行） |
| `scripts/upload_images.py` | 压缩并上传配图，换 mmbiz 地址 |
| `scripts/make_bundle.py` | 打包整条链路成 zip，用于换电脑 |
| `jingxuan-draft-push/scripts/push_to_wechat_draft.py` | 草稿箱推送（含覆盖保护） |
| `jingxuan-draft-push/scripts/make_cover.py` | 主题色封面 |
| `gzh-design-skill/scripts/validate_gzh_html.py` | 合规校验 |
