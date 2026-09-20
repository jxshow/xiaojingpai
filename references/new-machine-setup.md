# 换电脑：三步恢复完整流程

整条链路由 **4 个 skill + 1 份凭据** 组成。换机器只搬这 5 样，别的一概不用管。

## 需要什么

| # | 东西 | 位置（本机） | GitHub（私有） |
|---|---|---|---|
| 1 | 总控 SOP | `~/.workbuddy/skills/jingxuan-publish-flow` | `jxshow/jingxuan-publish-flow` |
| 2 | 排版引擎（4 主题） | `~/.workbuddy/skills/jingxuan-ai-gzh` | `jxshow/jingxuan-ai-gzh` |
| 3 | 草稿箱 API 推送 + 封面 | `~/.workbuddy/skills/jingxuan-draft-push` | `jxshow/jingxuan-draft-push` |
| 4 | 合规校验脚本 | `~/.workbuddy/skills/gzh-design-skill` | 上游原版，从 `isjiamu/gzh-design-skill` 取 |
| 5 | 凭据 | `~/.workbuddy/wechat/.env` | **不在任何仓库里**，需单独搬 |

`~` 在 Windows 上指 `C:\Users\<你的用户名>`。skill 放在用户级目录，所以**所有工作区共用**，跟项目目录无关。

---

## 方式 A：从 GitHub clone（推荐，可随时更新）

前 3 个是你的仓库，直接克隆到新机器的 skills 目录：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
SK="C:/Users/<新用户名>/.workbuddy/skills"
mkdir -p "$SK" && cd "$SK"

git clone https://github.com/jxshow/jingxuan-publish-flow.git
git clone https://github.com/jxshow/jingxuan-ai-gzh.git
git clone https://github.com/jxshow/jingxuan-draft-push.git

# 第 4 个是别人的上游项目
git clone https://github.com/isjiamu/gzh-design-skill.git
```

⚠️ 三个仓库都是**私有**的，新机器上第一次 clone 会要求登录 GitHub（浏览器授权或用 Personal Access Token）。

以后在这台机器改了东西，`git add -A && git commit -m "..." && git push`；
在另一台机器 `git pull` 即可同步。**不要在 .env 里放仓库里**。

## 方式 B：用打包好的 zip（没网/GitHub 不便时）

在本机生成搬运包：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
PY="C:/Users/xhshow/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" "C:/Users/xhshow/.workbuddy/skills/jingxuan-publish-flow/scripts/make_bundle.py"
```

产物在 `~/.workbuddy/bundles/jingxuan-publish-flow-<日期>.zip`（默认**不含**密钥）。

在新电脑上解压，把 `skills/` 下的 4 个文件夹整体复制到新机器的 `C:\Users\<新用户名>\.workbuddy\skills\`。

## 方式 C：直接从旧机器拷

把旧机器这 5 个路径原样拷到新机器相同位置：

```
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-publish-flow
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-ai-gzh
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-draft-push
C:\Users\<旧用户名>\.workbuddy\skills\gzh-design-skill
C:\Users\<旧用户名>\.workbuddy\wechat\.env
```

---

## 无论哪种方式，都要做这两件事

1. **放好凭据** —— 新建 `C:\Users\<新用户名>\.workbuddy\wechat\.env`：

   ```
   WECHAT_APPID=你的AppID
   WECHAT_APPSECRET=你的AppSecret
   ```

2. **重启 WorkBuddy**，让 skill 被重新加载。

## 新机器上要装的运行时

| 用途 | 要求 |
|---|---|
| 渲染 HTML | Node.js 18+（渲染器无第三方依赖） |
| 跑脚本 | Python 3.10+ |
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
PY="C:/Users/<用户名>/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK="C:/Users/<用户名>/.workbuddy/skills"

"$PY" "$SK/jingxuan-draft-push/scripts/push_to_wechat_draft.py" --check   # 凭据 + IP 白名单
node "$SK/jingxuan-ai-gzh/scripts/test.mjs"                              # 渲染器 24 项测试
node "$SK/jingxuan-ai-gzh/scripts/render_article.mjs" \
     "$SK/jingxuan-ai-gzh/assets/examples/agi-green.json" --out ./_smoke  # 渲染冒烟
```

三项都过，就可以直接发第一条口令了。
