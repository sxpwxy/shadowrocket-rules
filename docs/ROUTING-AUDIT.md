# 分流检查记录：2026-11-01

## 已完成的检查

- 联网获取并解析 32 个常规规则源、11 个选定 AI 社区源与官方语音地址，共 44 个来源。
- 校验下载内容非 HTML、声明 TOTAL 与正文一致、最小条数、语法、策略引用及生成地址；失败时不替换已发布数据。
- 两个主配置都保持 39 条规则，AI 域名优先于 Google/Facebook/Microsoft/Apple 等宽泛公司规则。
- 15 项自动测试通过，另外 41 个代表域名的静态分流样例通过。样例实际结果见 [routing-audit.json](../sources/routing-audit.json)，复查命令是 python3 scripts/audit_routes.py。
- General、Hosts、URL Rewrite、MITM 沿用已有配置；策略组和订阅筛选不在此次调整范围。

## AI 检查及补充

- ChatGPT/Gemini/Muse：核心域名加选定的共享登录、订阅、诊断与语音主机，具体证据及局限见 [AI-DOMAINS.md](AI-DOMAINS.md)。
- Claude：核对官方 Code/Desktop 网络要求，并新增 Anthropic 社区源自动同步。claude.app 等新产品根、MCP 内容与资源根纳入 AI。
- Cursor/Grok：核对官方新登录域名，补 accounts.spacex.ai、grokusercontent.com；其余主要认证/API/VM 根已覆盖。只将专用 S3 安装包桶补到普通代理的 AI工具下载。
- GitHub Copilot：核对官方允许列表，补用户管理 API、登录资源、遥测和实验服务；并未把整个 GitHub 网站、GitHub 内容 CDN 或 Azure 全部划入 AI。
- Windsurf/Devin：核对官方允许列表，既有产品域名及 static.devin.ai 已被后缀覆盖，补精确 apis.google.com，不接管整个 googleapis.com。
- Perplexity、Poe、Manus、ElevenLabs、JetBrains AI：重新获取现有社区源，既有域名、特定上传桶及资源主机仍被覆盖。
- Groq、Cerebras：重新检查社区根域名，与已有规则一致；Trae/Coze 参考现有国际域名条目，未把整个字节系域名或国内产品强制代理。
- Mistral、OpenRouter、Cohere、Kiro、CodeRabbit、Devin、Midjourney、Jasper、Lovart、Tripo 及其余已有图像/视频/研究工具：核对现有域名与原有来源。未获得完整官方网络清单的服务只保留已知根域覆盖，不宣称登录、支付、遥测、第三方 CDN 已完全捕获。
- 扩充社区已列出的 DeepWiki、Kimi 国际根、MiniMax 国际根、Qoder、Cline、OpenCode、Context7、Dify、AnythingLLM、Chutes、Duck.ai、Arena、Artificial Analysis。

## 常规规则检查

| 来源 | 发布条数 | 策略 | 结果 |
| --- | ---: | --- | --- |
| Lan | 142 | DIRECT | 格式、条数及样例检查 |
| SteamCN | 17 | DIRECT | 格式、条数及样例检查 |
| YouTube | 190 | YouTube | 格式、条数及样例检查 |
| Disney | 172 | Disney+ | 过滤 1 条共享 AWS 后缀 |
| HBO | 47 | Max | 过滤 2 条共享 AWS 后缀 |
| Spotify | 30 | Spotify | 格式、条数及样例检查 |
| Telegram | 40 | Telegram | 格式、条数及样例检查 |
| PayPal | 248 | PayPal | 格式、条数及样例检查 |
| Twitter | 33 | Twitter | 格式、条数及样例检查 |
| Facebook | 570 | Facebook | 格式、条数及样例检查 |
| Amazon | 205 | Amazon | 格式、条数及样例检查 |
| Sony | 116 | 游戏平台 | 格式、条数及样例检查 |
| Nintendo | 126 | 游戏平台 | 格式、条数及样例检查 |
| Epic | 15 | 游戏平台 | 格式、条数及样例检查 |
| Steam | 69 | 游戏平台 | 格式、条数及样例检查 |
| Game | 612 | 游戏平台 | 格式、条数及样例检查 |
| GitHub | 31 | PROXY | 格式、条数及样例检查 |
| Microsoft | 671 | 微软服务 | 格式、条数及样例检查 |
| Google | 698 | 谷歌服务 | 格式、条数及样例检查 |
| Apple | 1880 | 苹果服务 | 格式、条数及样例检查 |
| BiliBili | 127 | 哔哩哔哩 | 格式、条数及样例检查 |
| NetEaseMusic | 30 | DIRECT | 格式、条数及样例检查 |
| Baidu | 251 | DIRECT | 格式、条数及样例检查 |
| DouBan | 3 | DIRECT | 格式、条数及样例检查 |
| WeChat | 43 | DIRECT | 格式、条数及样例检查 |
| Sina | 108 | DIRECT | 格式、条数及样例检查 |
| Zhihu | 7 | DIRECT | 格式、条数及样例检查 |
| XiaoHongShu | 4 | DIRECT | 格式、条数及样例检查 |
| DouYin | 13 | DIRECT | 格式、条数及样例检查 |
| TikTok | 35 | TikTok | 格式、条数及样例检查 |
| Global | 36014 | PROXY | 格式、条数及样例检查 |
| China | 3753 | DIRECT | 格式、条数及样例检查 |

## 发现并处理的过宽视频规则

1. Disney 的 execute-api.us-east-1.amazonaws.com、HBO 的 execute-api.ap-southeast-1.amazonaws.com 和 execute-api.us-east-1.amazonaws.com 代表整片 AWS API Gateway 服务，不能仅据此判定某个租户是 Disney/Max。通过 sources/upstreams.json 的 exclude_rules 精确移除这三条。原始上游缓存保留。上游格式或排除项变动时构建会失败并要求复查，不悄悄忽略。
2. Max 旧补充中的 litix.io（Mux）和 brightline.tv（跨平台互动广告）不是 Max 专属。已从自有 Max 补充中移除，保留 discomax.com；其他原有内嵌匹配保留。它们随后仍可按普通全局规则访问，本次没有新增广告拦截。
3. 混合版有 30 个常规规则集直取上游，Disney/HBO 必须读取本仓库过滤版；镜像版全部读取本仓库。因此两个模式都不会绕过上述修正。

## 已知范围与限制

- 上述样例检查只模拟域名类规则，不是 Shadowrocket 引擎。不能证明所有设备、DNS、IP-only、UDP、登录、付款、语音和流媒体 DRM 都能正常工作。
- 上游公司级分类仍可能包含共享基础设施，例如 Amazon 包含 AWS/CloudFront，Microsoft 包含部分 Azure CDN，Google 包含通用 Google API；这是现有公司分组范围，不能误读为某个具体 App 的专属识别。更早的精确 AI 规则优先。
- Netflix 仍采用精简的专属域名列表，避免共享 AWS 后缀；IP-only 或特殊电视设备可能需要按日志补充。
- AI工具下载 的 Hugging Face/Ollama/LM Studio 域名也可能承载推理等行为，域名规则无法只识别“下载”。
- GitHub 网站登录、第三方连接器、企业自有 SSO/云模型网关、通用包管理器及资源 CDN 可能仍按普通分组访问。按域名分流不能保证整个 App 同一出口，也不能保证不会出现安全验证或地区限制。
- 官方允许列表用于放行网络连接，不等于该厂商推荐通过代理，也不证明某次请求传输了什么内容。
- 自动同步会刷新已列出的来源，不能自动发现所有新服务或官网新域名。手机还需要刷新远程规则集。

## 额外公开依据

- https://code.claude.com/docs/en/network-config
- https://code.claude.com/docs/en/desktop
- https://cursor.com/help/troubleshooting/sign-in-domains
- https://prod.cursor.com/docs/enterprise/network-configuration
- https://docs.github.com/en/copilot/reference/copilot-allowlist-reference
- https://docs.devin.ai/desktop/troubleshooting/windsurf-common-issues
- https://github.com/v2fly/domain-list-community/blob/master/data/anthropic
- https://github.com/v2fly/domain-list-community/blob/master/data/category-ai-!cn
- https://www.mux.com/docs/core/content-security-policy
- https://brightline.tv/our-team
