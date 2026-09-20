# 换电脑：三步恢复完整流程

整条链路由 **3 个 skill + 1 份凭据** 组成。换机器只搬这 4 样，别的一概不用管。

## 需要什么

| # | 东西 | 位置（本机） | 性质 |
|---|---|---|---|
| 1 | 总控 SOP | `~/.workbuddy/skills/jingxuan-publish-flow` | 本 skill，含可直接跑的脚本 |
| 2 | 排版引擎 | `~/.workbuddy/skills/jingxuan-ai-gzh` | 4 套主题 + 渲染器（= 你的定制版） |
| 3 | API 推送 | `~/.workbuddy/skills/jingxuan-draft-push` | 草稿箱 + 封面生成 |
| 3b | 合规校验 | `~/.workbuddy/skills/gzh-design-skill` | 只用到 `scripts/validate_gzh_html.py` |
| 4 | 凭据 | `~/.workbuddy/wechat/.env` | `WECHAT_APPID` / `WECHAT_APPSECRET` |

`~` 在 Windows 上指 `C:\Users\<你的用户名>`。skill 放在用户级目录，所以**所有工作区共用**，跟项目目录无关。

## 方式 A：用打包好的 zip（推荐）

在本机生成搬运包：

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
PY="C:/Users/xhshow/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" "C:/Users/xhshow/.workbuddy/skills/jingxuan-publish-flow/scripts/make_bundle.py"
```

产物在 `~/.workbuddy/bundles/jingxuan-publish-flow-<日期>.zip`（默认**不含**密钥）。

在新电脑上：

1. 解压，把 `skills/` 下的 4 个文件夹整体复制到新机器的 `C:\Users\<新用户名>\.workbuddy\skills\`
2. 新建 `C:\Users\<新用户名>\.workbuddy\wechat\.env`，内容：

   ```
   WECHAT_APPID=你的AppID
   WECHAT_APPSECRET=你的AppSecret
   ```

   （也可以从旧机器直接拷这个文件；它不在 zip 里是为了避免密钥进网盘）
3. 重启 WorkBuddy，让 skill 被重新加载

## 方式 B：直接从旧机器拷

把旧机器这 5 个路径原样拷到新机器相同位置：

```
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-publish-flow
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-ai-gzh
C:\Users\<旧用户名>\.workbuddy\skills\jingxuan-draft-push
C:\Users\<旧用户名>\.workbuddy\skills\gzh-design-skill
C:\Users\<旧用户名>\.workbuddy\wechat\.env
```

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

"$PY" "$SK/jingxuan-draft-push/scripts/push_to_wechat_draft.py" --check        # 凭据 + IP 白名单
node "$SK/jingxuan-ai-gzh/scripts/test.mjs"                            # 渲染器 24 项测试
node "$SK/jingxuan-ai-gzh/scripts/render_article.mjs" \
     "$SK/jingxuan-ai-gzh/assets/examples/agi-green.json" --out ./_smoke   # 渲染冒烟
```

三项都过，就可以直接发第一条口令了。
