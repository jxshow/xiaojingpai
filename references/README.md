# 鲸选AI 公众号发布流水线

把一篇腾讯文档，排成鲸选AI 风格的公众号文章，配好图和重点，直接写进公众号草稿箱。

## 平时怎么用

在 WorkBuddy 里发一句**中文**就行，不用打英文 skill 名：

```
用 AGI绿 排版这篇，配图 + 重点标粗下划线，推到草稿箱：

https://docs.qq.com/doc/XXXX
```

最省事的写法：`排这篇推草稿箱：<链接>`（默认 AGI绿）。

更多说法（换主题、只预览、更新已有草稿、关键词怎么念）见同目录的 **口令卡.md**。

## 整条链路

```
腾讯文档 ──读原文/加粗──▶ article.base.json ──apply_marks──▶ article.json
                                                              │
                                                     render_article.mjs
                                                              ▼
                                                        article.html
                                                    （合规校验 + 预览）
                                                              │
                    官方新闻稿抓图 ──upload_images──▶ mmbiz 地址 ┘
                                                              ▼
                                       make_cover + push_to_wechat_draft
                                                              ▼
                                                        公众号草稿箱
```

## 用了哪些 skill

| skill | 作用 |
|---|---|
| `jingxuan-publish-flow` | 总控：流程、脚本、口令（**入口看这里**） |
| `jingxuan-ai-gzh` | 排版引擎：4 套主题（字节绿 / AGI绿 / 杂志绿 / Pro蓝）+ 确定性渲染器 |
| `jingxuan-draft-push` | 官方 API 推送草稿箱 + 主题色封面生成 |
| `gzh-design-skill` | 上游原版，只用到它的 `validate_gzh_html.py` 合规校验 |

## 默认约定

| 项 | 值 |
|---|---|
| 主题 | AGI绿（`agi-green`），主色 `#2ea250` |
| 作者 | `鲸选AI` |
| 封面 | 900×383，同主题色 |
| 重点 | 整句 `strong` 黑粗 + 短关键词 `underline` 2px 主题色下划线，不自行编造 |
| 英文标签 | 原文有才写，没有就省略整行 |
| 来源 | 官方新闻稿优先；图注标图源 |

## 安全底线

1. **只用官方 API 推草稿箱，不开浏览器扫码登录。**
2. **`draft/update` 是整篇替换** —— 后台被手工改过就拒绝覆盖，先问再用 `--force`。
3. **不擅自改写原文**：文字、顺序、数字、链接一律保真；只做排版和既有的强调。
4. `.env` 含明文密钥，不进仓库、不发截图、不传公开网盘。

## 仓库

三个自建 skill 都在 GitHub（私有），可以 clone 到任何电脑：

| skill | 仓库 |
|---|---|
| `jingxuan-publish-flow` | `jxshow/jingxuan-publish-flow` |
| `jingxuan-ai-gzh` | `jxshow/jingxuan-ai-gzh` |
| `jingxuan-draft-push` | `jxshow/jingxuan-draft-push` |

凭据 `.env` **不在任何仓库里**，换机器要单独搬。

## 换电脑

见 `install.md`。三种方式任选：从 GitHub clone（推荐，可随时 pull 更新）、用打包 zip、直接拷目录。
无论哪种，最后都要放好 `.env` + 把新机器的公网 IP 加进公众号后台白名单。
