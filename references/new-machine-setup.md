# 换电脑：三步恢复完整流程

整条链路叫 **小鲸排 Skill**（英文名 `xiaojingpai`），由 **3 个 skill + 1 份凭据** 组成。
换机器只搬这 4 样，别的一概不用管。

> **最省事的方式**：新机器上直接跟 Agent 说
> 「帮我装这三个 skill：`https://github.com/jxshow/xiaojingpai`、
> `https://github.com/jxshow/xiaojingpai-render`、`https://github.com/jxshow/xiaojingpai-push`，
> 装完检查依赖、把 `~/.workbuddy/wechat/.env` 也接过来」——它会自己 clone 和检查。
> 本文是手动操作的完整步骤，留给 Agent 帮不上忙、或你想自己确认细节的时候。

## 需要什么

| # | 东西 | 位置（本机） | GitHub（私有） |
|---|---|---|---|
| 1 | 总控 SOP + 合规校验 | `~/.workbuddy/skills/xiaojingpai` | `jxshow/xiaojingpai` |
| 2 | 排版引擎（4 主题） | `~/.workbuddy/skills/xiaojingpai-render` | `jxshow/xiaojingpai-render` |
| 3 | 草稿箱 API 推送 + 封面 | `~/.workbuddy/skills/xiaojingpai-push` | `jxshow/xiaojingpai-push` |
| 4 | 凭据 | `~/.workbuddy/wechat/.env` | **不在任何仓库里**，需单独搬 |

`~` 在 Windows 上指 `C:\Users\<你的用户名>`。skill 放在用户级目录，所以**所有工作区共用**，跟项目目录无关。

> 早期版本还要额外装一个上游 skill（`gzh-design-skill`）来跑合规校验。
> 现在校验脚本已内联进 `xiaojingpai/scripts/validate_html.py`，**不用再装它了**。

---

## 方式 A：从 GitHub clone（推荐，可随时更新）

三个仓库都是你的，直接克隆到新机器的 skills 目录：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
SK="C:/Users/<新用户名>/.workbuddy/skills"
mkdir -p "$SK" && cd "$SK"

git clone https://github.com/jxshow/xiaojingpai.git
git clone https://github.com/jxshow/xiaojingpai-render.git
git clone https://github.com/jxshow/xiaojingpai-push.git
```

⚠️ 三个仓库都是**私有**的，新机器上第一次 clone 会要求登录 GitHub（浏览器授权或用 Personal Access Token）。

以后在这台机器改了东西，`git add -A && git commit -m "..." && git push`；
在另一台机器 `git pull` 即可同步。**不要把 .env 放进仓库。**

## 方式 B：用打包好的 zip（没网/GitHub 不便时）

在本机生成搬运包：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
PY="C:/Users/xhshow/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" "C:/Users/xhshow/.workbuddy/skills/xiaojingpai/scripts/make_bundle.py"
```

产物在 `~/.workbuddy/bundles/xiaojingpai-<日期>.zip`（默认**不含**密钥）。

在新电脑上解压，把 `skills/` 下的 3 个文件夹整体复制到新机器的 `C:\Users\<新用户名>\.workbuddy\skills\`。

## 方式 C：直接从旧机器拷

把旧机器这 4 个路径原样拷到新机器相同位置：

```
C:\Users\<旧用户名>\.workbuddy\skills\xiaojingpai
C:\Users\<旧用户名>\.workbuddy\skills\xiaojingpai-render
C:\Users\<旧用户名>\.workbuddy\skills\xiaojingpai-push
C:\Users\<旧用户名>\.workbuddy\wechat\.env
```

---

## 无论哪种方式，都要做这两件事

1. **放好凭据** —— 新建 `C:\Users\<新用户名>\.workbuddy\wechat\.env`：

   ```
   WECHAT_APPID=你的AppID
   WECHAT_APPSECRET=你的AppSecret
   ```

   AppID / AppSecret 在公众号后台「设置与开发 → 基本配置」里拿。

2. **重启 WorkBuddy**，让 skill 被重新加载。

## 新机器上要装的运行时

| 用途 | 要求 |
|---|---|
| 渲染 HTML | Node.js 18+（渲染器无第三方依赖） |
| 跑脚本 | Python 3.10+（校验/推送/注入都是纯标准库） |
| 压缩封面/配图 | Python 包 `Pillow` |

安装 Pillow（用隔离 venv，别装全局）：

```bash
"<python.exe>" -m venv ~/.workbuddy/binaries/python/envs/default
~/.workbuddy/binaries/python/envs/default/Scripts/pip install Pillow
```

## 两个必须注意的坑

1. **IP 白名单**：新机器的公网 IP 不在公众号后台白名单里，推送会报 `40164`。去
   公众号后台 → 设置与开发 → 基本配置 → IP 白名单，把新 IP 加进去。
   先用 `push_to_wechat_draft.py --check` 探一下就知道。
2. **Git Bash 的环境变量**：Windows 上跑脚本前先
   `export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"`，
   并且路径一律写 `C:/...` 而不是 `/c/...`。

## 自检

新机器上跑一遍，全绿就说明搬好了：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
PY="C:/Users/<用户名>/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK="C:/Users/<用户名>/.workbuddy/skills"

"$PY" "$SK/xiaojingpai-push/scripts/push_to_wechat_draft.py" --check   # 凭据 + IP 白名单
node "$SK/xiaojingpai-render/scripts/test.mjs"                          # 渲染器 24 项测试
node "$SK/xiaojingpai-render/scripts/render_article.mjs" \
     "$SK/xiaojingpai-render/assets/examples/agi-green.json" --out ./_smoke  # 渲染冒烟
"$PY" "$SK/xiaojingpai/scripts/validate_html.py" --help                 # 合规校验可用
```

四项都过，就可以直接发第一条口令了（`排这篇推草稿箱：<链接>`）。
