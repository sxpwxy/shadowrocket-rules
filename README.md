# 小火箭：精简主配置 + 自有 GitHub 规则集

这份仓库把上一版 607 条主文件规则拆成 **39 条主规则**，主要内容放进独立的 RULE-SET 文件。提供两套互为替代的配置：

| 文件 | 常规规则来源 | AI 和个人补充 |
| --- | --- | --- |
| `config/Shadowrocket.conf`（推荐） | 30 个常规规则集直取原作者；Disney/HBO 用本仓库过滤版 | 从本仓库读取 |
| `config/Shadowrocket-mirror.conf` | 所有 37 个 RULE-SET 均读取本仓库，Actions 同步上游 | 从本仓库读取 |

本仓库地址：https://github.com/sxpwxy/shadowrocket-rules

## 直接导入小火箭

两个配置选一个即可，推荐第一个：

- [推荐：常规规则直连上游](https://raw.githubusercontent.com/sxpwxy/shadowrocket-rules/main/config/Shadowrocket.conf)
- [可选：全部规则读取本仓库镜像](https://raw.githubusercontent.com/sxpwxy/shadowrocket-rules/main/config/Shadowrocket-mirror.conf)

在小火箭「配置」中通过 URL 下载，点选启用，全局路由设为「配置」。主页选普通订阅节点，AI 组选优质订阅的具体节点。**AI 初始为 REJECT，导入后必须先改选节点。**

仓库只保存公开规则和配置模板，不含节点订阅、密码、个人服务器地址或 GitHub Token。节点在手机内选择。同步结果可在 Actions 与 `sources/last_sync.json` 查看。

## 复制到其他 GitHub 仓库（可选）

1. 在 GitHub 创建一个用于公开规则的 **Public 仓库**，默认分支建议 `main`。私有仓库的普通 Raw 地址不能作为免登录规则源，本方案不把访问 Token 放进 URL。
2. 解压，把本目录**里面的内容**上传到仓库根目录。不要只上传 ZIP，也不要再套一层目录。
3. 必须包含 `.github/workflows/update-rules.yml`。Mac Finder 可用 `Command + Shift + .` 显示隐藏目录；命令行 `git add .` 会包含它。
4. 打开仓库 **Actions → Update routing rules → Run workflow**。首次 push 也可能自动启动。若需要，先允许该仓库运行 Actions。
5. 等待成功，打开仓库根目录的 `IMPORT_URLS.txt`。里面是脚本根据你的仓库名和分支生成的真实配置链接。
6. 两个链接选一个导入。建议先选 `config/Shadowrocket.conf`。两个模式不需要同时使用。
7. 在小火箭中启用配置、全局路由选“配置”。主页选普通订阅节点，AI 组选优质订阅的具体节点。**AI 初始为 REJECT，必须先改选节点。**

也可以在本地生成：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/sync_rules.py --repo 你的用户名/你的仓库名 --branch main
```

测试只使用包内缓存。生成命令会联网获取上游；需要离线构建时加 `--offline`，但离线构建不代表数据已更新。

## 2026-11-01 辅助域名与其他 AI 检查

已将选定的共享登录、订阅和诊断主机默认合并到 AI 规则集，包括 Google OAuth、日志里出现的 Meta Graph、RevenueCat、区域 Sentry，以及 Cursor 新登录和 GitHub Copilot 相关主机。**其他 App 访问相同共享主机也会使用 AI 出口。**

完整范围、逐项来源和不能保证的部分见 [域名说明](docs/AI-DOMAINS.md)、[检查记录](docs/ROUTING-AUDIT.md) 和 [证据表](sources/AI-dependencies-evidence.csv)。辅助主机编辑 `custom/AI-Dependencies.list`；`include_shared_ai_hosts=false` 只表示未额外启用更广的候选清单，不会关闭这批已选补充。

## 更新链路

原作者更新规则 → GitHub Actions 获取和校验 → 合并你的补充 → 写回本仓库 → 小火箭刷新规则集。

现有 32 个常规规则来源继续同步；AI 的选定社区来源现为 11 个（增加 Anthropic）。

主文件里一条 RULE-SET 引用可以展开成很多实际匹配项。39 条表示入口简洁，不是运行时只剩下 39 条匹配条件；把规则装进列表也不自动提升速度。

- 默认 Actions 每天 UTC+8 **06:23** 尝试同步一次，也支持手动 Run workflow。
- GitHub 的定时运行可能延迟；公开仓库长期不活跃时，定时任务可能被停用，需在 Actions 检查。
- 混合模式：YouTube 等 30 个常规来源在小火箭刷新时直取上游，Disney/HBO 先经本仓库过滤共享 AWS 后缀，AI 和个人文件仍等本仓库 Actions 同步。
- 镜像模式：手机只读你的仓库，所有来源的新内容都要先经过 Actions，可能多一段同步延迟。
- 单纯复制文件或 Fork 一次，不会自动跟随未来的上游更新。
- 刷新规则集只能拿到 URL 当前内容；“重新下载”不是“自动发现新 AI 服务”。脚本会同步已列出的社区服务文件和官方语音数据。未来新品牌、新独立域名若没有进入选定上游或个人补充，仍需加入。

上游维护频率由各作者决定；不保证每日变更，不因日期旧就认定失效。

## 手机端怎样刷新又不覆盖节点选择

- 手动：配置 → 当前配置 → 使用配置 / 编译配置，以获取引用的远程规则资源。
- 本地保存一份不带主配置更新地址的配置，可让规则集继续远程更新，同时在本地保留节点、订阅筛选等设置。
- 主配置本身的自动覆盖更新可能重置你在手机上改过的选项。别把“更新规则集”与“整个配置文件覆盖更新”当成同一操作。
- 确需自动更新主配置时，把长期设置写在仓库的 `settings.json` 或 `templates/groups.conf`；手机上的临时选择仍应复查。

## PROXY 和 REJECT 是什么，是否必须保留

- `PROXY`：使用默认代理，普通手动选择方式下是主页当前节点。这是一个方便的候选项，方便临时让 AI 跟随主页；不是必需，也不代表所有 AI 自动同时走普通节点。
- `REJECT`：拒绝连接。放在 AI 组里是一个“暂停 AI 网络”的选项，并作为初始状态，避免还没选定优质节点就自动使用错误出口；不是做分流的必需条件，也不是坏节点的标签。
- `select`：手动单选。只有当前选中的候选项参与路由，其余节点只是备选。
- `.*`：匹配所有节点名。未限定订阅时，所有订阅的节点都可能列入候选；并不把所有 App 的流量归 AI。

如果要让 AI 组只显示优质订阅，把 `settings.json` 的 `ai_subscription` 改成小火箭里该订阅的准确名称，例如：

```json
{
  "ai_subscription": "我的优质订阅",
  "include_shared_ai_hosts": false
}
```

改动会触发构建。生成配置将限定该订阅；导入后仍要选定具体节点。或者仅在手机内设置订阅筛选，不更新整个主文件。

## 哪些文件自己维护

| 文件 | 怎么用 | 自动同步会不会覆盖 |
| --- | --- | --- |
| `custom/AI-extra.list` | 自己补充的 AI 域名，不带策略列 | 不覆盖 |
| `custom/AI-Dependencies.list` | 已启用的选定共享登录、订阅、诊断主机 | 不覆盖 |
| `custom/AI-exclude.list` | 从合并结果删除完全相同的规则行 | 不覆盖 |
| `custom/AI-shared-optional.list` | 公共登录、挑战、支付等，可选启用 | 不覆盖 |
| `custom/Netflix-Core.list` | Netflix 精简域名，避免共享 AWS 后缀误分组 | 不覆盖 |
| `custom/AI-Tools.list` | 模型下载与同域推理服务，默认普通代理 | 不覆盖 |
| `custom/Max-Extra.list` | Max 补充 | 不覆盖 |
| `sources/ai-upstreams.json` | 选定的社区 AI 服务来源 | 不覆盖 |
| `sources/upstreams.json` | 32 个常规规则的地址、格式和策略 | 不覆盖 |
| `templates/groups.conf`、`settings.json` | 策略组与订阅筛选 | 不覆盖 |
| `rules/**`、`config/**` | 自动生成的文件 | 会重建，勿在这里手改 |

例如在 AI-extra.list 中加入：

```text
DOMAIN-SUFFIX,muse.ai
DOMAIN,my-confirmed-api.example.com
```

提交后 Actions 会重建。注意：根域名后缀会匹配它的全部子域名。仅删除一条子域名规则，不能抵消另一条已包含它的父域名后缀规则；这种例外应移除父规则，或在主配置中添加更高优先级的路由。

## 保持了什么、改变了什么

- General、Host、URL Rewrite、MITM 沿用上一版，不修改设备系统网络设置。
- 上一版的 AI 域名、402 条语音 IP 逻辑规则及其他内嵌路由按用途拆进规则集；本次移除两条非 Max 专属的共享统计/广告后缀，其他既有内嵌匹配保留。选定上游可以继续增加匹配项。
- 官方语音地址仅匹配 UDP 3478。语音的新 IP 会从 OpenAI JSON 同步；协议、端口或 JSON 格式改变时脚本需要维护。
- AI 仍优先于宽泛的 Google / Microsoft / Facebook / X / TikTok 列表。
- 常规列表镜像会把 Quantumult X 的 HOST 等语法转换成 Shadowrocket 的 DOMAIN 等语法，移除源文件自带的策略标签，由主配置指定策略。
- 过宽的共享 AI 后缀会被过滤，列表在代码的 BLOCK_AI 中。选定共享依赖现默认进入 AI；更广候选仍需手动启用。
- Netflix 保留精简策略，因此特殊设备、IP-only 连接等仍可能需按日志补充。
- 主文件数量减少不等于匹配总量减少，也不代表完整实机兼容性已验证。

## 校验和失败处理

脚本只下载公开文本和官方语音 JSON，不执行上游脚本。所有来源先在内存里解析和校验，再写入生成文件。

- 下载失败、HTML 错误页、正文条数与上游 TOTAL 不符、意外空列表或不支持的新语法：本次构建失败，旧版已发布数据保留。
- 不会用一个空文件替换旧的可用规则，也不会假装旧缓存是刚刚同步的数据。
- `sources/last_sync.json` 记录成功构建和来源摘要；缓存的日期不是服务可用性保证。
- 保护会检查基础格式与过宽后缀，不能识别所有语义错误。仍需在手机上检查规则命中、实际节点和服务连接。

本地检查：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/sync_rules.py --offline --repo 你的用户名/你的仓库名 --branch main
```

已在 GitHub Actions 成功运行测试、联网同步和写回。尚未在用户 iPhone 的 Shadowrocket 引擎及个人节点上实测。

## 来源和许可

- LOWERTOP/Shadowrocket：原配置架构和基础网络设置。
- v2fly/domain-list-community：选定 AI 服务域名，MIT，许可见 `licenses/MIT-v2fly.txt`。
- blackmatrix7/ios_rule_script：常规服务规则和镜像来源，GPL-2.0，许可见 `licenses/GPL-2.0-blackmatrix7.txt`，对应可编辑来源缓存和生成脚本一并保留。
- OpenAI：公开的 [chatgpt-voice.json](https://openai.com/chatgpt-voice.json)。
- `sources/AI-extra-evidence.csv`：上一版个人 AI 补充的逐项来源。

本仓库的整合代码按 GPL-2.0 提供，根目录 LICENSE 为许可原文；第三方内容保留各自归属。这里只存公开规则，不要向公开仓库上传任何节点订阅链接、节点密码或个人 Token。

官方行为参考：

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://github.com/LOWERTOP/Shadowrocket
