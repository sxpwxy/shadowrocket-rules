# ChatGPT、Gemini、Meta Muse 的域名与出口范围

本页记录 2026-11-01 对官方文档、上游规则和手机连接记录的核对。它是已知目的地址的路由清单，不是完整抓包报告，也不保证一个 App 的所有连接均已覆盖。

本次也核对其他已收录 AI 的社区源，并对照 Claude、Cursor、Windsurf/Devin、GitHub Copilot 的官方网络要求。详见 [检查记录](ROUTING-AUDIT.md)。

## 已覆盖的核心服务

| 服务 | 主要域名或主机示例 | 路由 |
| --- | --- | --- |
| ChatGPT | chatgpt.com、openai.com、oaistatic.com、oaiusercontent.com；其中 ws.chatgpt.com、ios.chat.openai.com 已被父域名后缀覆盖 | AI |
| Gemini | gemini.google.com、gemini.gstatic.com、robinfrontend-pa.googleapis.com、geller-pa.googleapis.com、generativelanguage.googleapis.com 等 | AI |
| Muse | muse.ai、meta.ai、metaaivm.com、metaaiusercontent.com；hatch-api.meta.ai、hatch.metaaivm.com 已被后缀覆盖 | AI |
| ChatGPT 实时语音 | 官方 chatgpt-voice.json 中的目的 IP，仅 UDP 3478 | AI |

完整有效域名清单在 [AI.list](../rules/ai/AI.list)，可编辑的补充在 [AI-Dependencies.list](../custom/AI-Dependencies.list)。逐条来源、用途及不确定性在 [证据表](../sources/AI-dependencies-evidence.csv)。

## 本次默认启用的辅助域名

共 40 条规则。包括 WorkOS 登录资源、Cloudflare 挑战、Stripe 支付脚本、RevenueCat 订阅、特定 Sentry/Datadog 接收主机、LiveKit 中继、Google 账户及令牌接口，以及手机日志中的三个 Meta Graph 主机。它们与已有核心规则合并到同一个 AI.list，主配置仍为 39 条规则。

- 官方“允许列表”说明网络应允许访问，不代表每个客户端每次一定访问，也不是官方的代理分流建议。
- Google 的 accounts.google.com、oauth2.googleapis.com，以及 RevenueCat、WorkOS、Stripe、Cloudflare、LiveKit 等主机会被其他服务共用。其他 App 访问相同主机也会走 AI。
- meta.graph.meta.com、ar.graph.meta.com、graph.facebook.com、signaler-pa.googleapis.com 的手机日志只能证明目的主机和匹配策略，不能证明特定 URL 的功能或唯一发起 App。
- webchannel-robinfrontend-pa.googleapis.com 与 robinfrontend-pa.googleapis.com 是并列主机。后缀规则不匹配名字前多了连字符的并列主机；这里单独补入。
- shortwave.facebook.com 来自一手 Muse 桌面客户端研究，仅提取公开目的主机，不下载或运行研究代码。iOS 是否使用需以本机记录为准。
- Muse 的官方资料说明部分工作发生在云端专用虚拟机。手机分流只影响手机发起的连接，不能控制云端 Muse 自己浏览网站时的出口。
- 不把整个 googleapis.com、google.com、meta.com、facebook.com、sentry.io、revenuecat.com、Apple 或共享云平台后缀划入 AI；不声称全部广告、系统证书或 iCloud 邮件流量属于 AI。
- 保留 Apple StoreKit、App Store、证书检查、iCloud 邮件及未知通用广告/分析域名的现有路由。它们可能与系统或多个 App 有关，不能仅因时间相近就全部收进 AI。

## 如何维护与刷新

1. 日常补充修改 custom/AI-Dependencies.list 或 custom/AI-extra.list；Actions 会自动构建。
2. daily sync 会保留这两个自定义文件，并持续获取已配置的 11 个社区服务文件及官方语音 IP。官方网页上的新域名、未知新服务不会自动被发现或抓取。
3. 当前用户已要求纳入这批选定共享依赖，因此 AI-Dependencies.list 默认合并；settings.json 的 include_shared_ai_hosts 仍为 false，它只控制另一个更广的候选文件。
4. 如要撤销某条补充，可在自定义文件删除它，或在 AI-exclude.list 放入完全相同的规则行。若仍有另一条父域名后缀覆盖它，必须同时处理父规则。
5. 主配置导入地址不变。手机重新使用/编译当前配置以获取远程规则集，更新后断开重连，并重新打开待测 App；核对一条新日志的策略和具体节点。
6. 多域名与共享依赖意味着这仍是按目的域名分流，不能保证按 App 绑定全部流量，也不能保证不发生账号安全验证或地区限制。

## 公开来源

- [OpenAI 网络要求](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [OpenAI 文档中的区域 Sentry 主机](https://learn.chatgpt.com/docs/enterprise/govcloud-configuration)
- [RevenueCat 的 ChatGPT 合作案例](https://www.revenuecat.com/customers/revenuecat-openai)
- [Google OAuth 文档](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google AI 社区域名表](https://github.com/v2fly/domain-list-community/blob/master/data/google-deepmind)
- [Gemini iOS 的 WebChannel 一手报告](https://github.com/MetaCubeX/meta-rules-dat/issues/170)
- [Meta Muse 官方页面](https://ai.meta.com/muse/)
- [Meta Muse 的安全架构](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse)
- [Muse 客户端公开研究中的目的主机](https://github.com/pwardle/not-a-mused/blob/main/notamused.py)


## 其他已核对服务与共享依赖

- Claude API、认证、MCP 内容及资源的主要官方主机已被 Anthropic/Claude 后缀覆盖；新增 Anthropic 上游每天同步。Claude Code 官方列出的两个可选 Datadog 主机精确纳入。
- Cursor 原有五个产品后缀覆盖 API、认证、VM 及资源；新增 accounts.spacex.ai 和 grokusercontent.com，其他新认证主机已被 x.ai/grok.com 后缀覆盖。官方指定的 S3 安装包桶放入 AI工具下载。
- GitHub Copilot 增补 api.github.com、登录资源、遥测及实验配置主机；github.com 网页本身保持原有普通代理。故 GitHub 登录全流程仍可能有不同出口，需要完整一致时再明确调整 GitHub 的路由。
- Windsurf/Devin 的产品后缀已覆盖，新增精确 apis.google.com 认证主机；不照搬官方防火墙建议中的整个 googleapis.com 后缀。
- 另补 DeepWiki、Kimi 国际域名、MiniMax 国际域名、Qoder、Cline、OpenCode、Context7、Dify 等社区已收录根域名；不据此认定其国内版本必须走海外节点。
- 存储桶、包管理器、通用字体及 JavaScript CDN 可能被多个应用使用。未将整个 storage.googleapis.com、npm、GitHub、Cloudflare 或全部 CDN 强制纳入 AI。

2026-11-01 后续日志补充：graph.facebook.com 与 meta.graph.meta.com 是不同的完整主机。前者现以 DOMAIN 精确加入；www.facebook.com 现按用户明确要求精确加入 AI；整个 facebook.com 后缀及其他未单列子域仍保持原分组。其他 App 对 graph.facebook.com 的访问也会走 AI，不能仅凭日志推断具体请求内容或唯一发起 App。

2026-11-01 用户追加要求：将 www.facebook.com 以 DOMAIN 精确路由到 AI，不把整个 facebook.com、fbcdn.net 或 cdninstagram.com 加入 AI。其他 App 或浏览器访问该完整主机也会使用 AI 出口；该主机流量不保证只包含登录或少量数据。
