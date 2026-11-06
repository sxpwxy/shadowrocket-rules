# 在现有配置中新增币圈分流

规则覆盖交易所、钱包、行情/图表、区块浏览器、常用 Web3/DeFi 和部分相关资讯/支付域名，不限于 Bybit、币安和 OKX。名单来自社区分类与官方域名补充，并不保证涵盖每个 App 的全部连接，也不是登录、下载或投资推荐清单。

本功能独立于现有 AI 和视频分流。**不需要重新导入整个主配置**；新增一个策略组和一条规则集引用即可。默认主配置仍是 39 条主规则，币圈引用由你添加到本机正在使用的配置。

## 两种客户端的地址

| 客户端 | 规则集 URL | 内容格式 |
| --- | --- | --- |
| Shadowrocket | https://raw.githubusercontent.com/sxpwxy/shadowrocket-rules/main/rules/crypto/Crypto.list | DOMAIN / DOMAIN-SUFFIX，无策略列 |
| FlClash / Mihomo | https://raw.githubusercontent.com/sxpwxy/shadowrocket-rules/main/rules/crypto/Crypto.yaml | YAML payload；behavior=classical，format=yaml |

两份文件由同一份合并数据生成，匹配范围相同。扩展名本身不能决定兼容性，解析格式必须与正文对应。

## Shadowrocket

1. 打开当前启用的配置，在代理分组中新增名称为「币圈」的手动选择组（select）。添加你已有订阅中的候选节点，并选定一个具体节点。节点及订阅名称只在本机配置。
2. 在同一配置的规则中新增：类型 `RULE-SET`，内容为上面的 `Crypto.list` URL，策略为「币圈」。
3. 把这条引用放在局域网直连规则之后、国内/宽泛服务规则及 GEOIP、FINAL 之前。已有 AI、视频、Telegram 引用保留。
4. 保存并使用/编译当前配置，确认全局路由使用「配置」。重新建立连接后检查「币圈」组选中的节点。

规则文本是：

```ini
RULE-SET,https://raw.githubusercontent.com/sxpwxy/shadowrocket-rules/main/rules/crypto/Crypto.list,币圈
```

需要文本合并示例时，参考 [Crypto-Shadowrocket-addon.conf](../config/Crypto-Shadowrocket-addon.conf)。它只有新增片段，不能作为完整配置启用。示例组初始为 REJECT，合并后先选节点；`.*` 只是列出所有节点名，不会把所有流量都分给币圈，也不会限定优质订阅。可在本机按订阅筛选。

## FlClash

以下沿用你已经找到的「自定义配置资源」和「日常分流」页面；不同版本入口位置可能不同。

1. 在「日常分流」的策略组旁点 ＋，新增「币圈」，类型选手动选择（Selector）。候选来源选择已有订阅/节点；之后在代理页面为此组选定节点。这里只创建组还不会产生分流。
2. 进入「自定义配置资源 → 规则集」，通过 URL 添加上面的 `Crypto.yaml`，名称可填「币圈规则」。类型为远程，行为选 `classical`，文件格式选 `yaml`；如能设置更新间隔，可用 86400 秒。
3. 返回「日常分流 → 规则 → 添加」，类型选 `RULE_SET`，规则集选「币圈规则」，分流策略选「币圈」。「不解析主机名」和「匹配来源 IP」保持关闭；本规则集只有域名规则。
4. 按下面的顺序排列并保存，确保正在使用「日常分流」，运行模式选「规则」。

| 从上往下 | 策略 |
| --- | --- |
| 局域网规则 | DIRECT |
| 币圈规则 | 币圈 |
| AI | 保持现有 AI 组 |
| YouTube | 保持现有 YouTube 组 |
| Telegram | 保持现有 Telegram 组 |
| 国内规则 | DIRECT |
| GEOIP,CN | DIRECT |
| MATCH | 保持现有日本节点组或你已有的兜底代理组 |

这是便于检查的顺序，不要求重建现有条目。MATCH 必须位于末尾；把币圈放在宽泛的国内/服务规则之前，避免先被它们命中。不要额外新增第二条 MATCH。

如果用 YAML 编辑，参考 [Crypto-Mihomo-addon.yaml](../config/Crypto-Mihomo-addon.yaml)。这是合并片段；将 provider 占位名称换成已有订阅集合名称，分别合并到现有 `proxy-groups`、`rule-providers`、`rules`，不要覆盖原有内容或直接作为完整订阅导入。

## 覆盖范围与共享连接

典型覆盖包括 Binance、Bybit、OKX、Gate、Bitget、MEXC、KuCoin、Kraken、Coinbase、HTX、Crypto.com、Upbit；MetaMask、Phantom、Trust Wallet、OneKey、SafePal、Ledger、Trezor、Rabby、Exodus；CoinMarketCap、CoinGecko、CoinGlass、TradingView、DEX Screener、Dune、DefiLlama、Nansen；Etherscan、BscScan、Tronscan、Solscan、Mempool；Uniswap、Aave、PancakeSwap、DeBank、WalletConnect 等。

- 域名后缀会覆盖其子域名，因此平台自有域名下的登录、API、WebSocket、图片通常一并匹配；独立域名需要单独列入。
- `gemini.com` 是交易所的域名；Google Gemini 的 `gemini.google.com` 不会因此归入币圈。
- TradingView 同时提供股票等非币圈图表；该站的其他功能也会随本组路由。
- 同一个 App 可能访问 Google/Apple 登录、共享验证码、KYC、客服、广告或统计平台。不能仅凭域名辨认由哪个 App 发起，未整体接管这些公共平台根域名；现有 AI 规则已收录的共享登录主机仍可能走 AI 组。
- 仅保留来源中明确列出的独立租户主机，不将整个 AWS、CloudFront、GitHub Pages、AppsFlyer、Zendesk 等共享服务归为币圈。已跳过宽泛关键词和 Windows 进程规则，保证两个客户端使用相同域名范围。
- 上游保留的一些历史品牌域名可能已不再提供服务。规则只用于分类，不代表域名仍有效或站点可信。

为了减少出口变动，可以让币圈组手动选定稳定节点。URLTest 会按测速结果切换；不希望账号使用中换出口时，不把币圈指向此类组。分流只决定连接出口，不改变平台的地区、身份或使用资格要求，也不能保证不会触发验证。

## 检查是否生效

打开常用平台的公开首页/行情页即可检查，不需要充值、下单或提供密钥。到客户端连接记录查看实际主机、命中规则、代理链及最终节点，应该能看到币圈规则集和币圈组选中的节点。不同平台自有域名应落入同一组；共享服务按实际命中的规则处理。

更新后先关闭旧连接再重新打开页面，既有连接可能继续使用旧路由。若仍命中 MATCH，记录完整主机名核对；不要凭目标 IP 或地理标签直接加入整段 IP。源地址、目标位置也不等于最终代理出口地区。

## 来源、更新与验证边界

- [MetaCubeX category-cryptocurrency](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/classical/category-cryptocurrency.yaml)
- [blackmatrix7 Crypto](https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Clash/Crypto/Crypto.list)
- [blackmatrix7 Binance](https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Clash/Binance/Binance.list)
- 人工补充来源见 [证据表](../sources/crypto-evidence.csv)；修改 `custom/Crypto-extra.list` 和 `custom/Crypto-exclude.list`，不要手改生成文件。

现有 Actions 每天 UTC+8 06:23 尝试拉取上游，校验后生成两种格式；GitHub 调度可能延迟。客户端也要刷新自己的远程规则集，链接保持不变。脚本下载失败、条数异常或出现未知语法时不发布本次结果，继续保留上次已发布版本。

构建记录见 [crypto-last-sync.json](../sources/crypto-last-sync.json)，包括来源摘要、跳过/排除规则、静态匹配样本及成功获取时间。`offline_build=true` 只代表离线生成，不能作为刚刚同步的证明。

测试验证了格式、两种输出一致性、典型主机匹配及共享域名不被过宽捕获。尚未在你的客户端、节点、各交易所登录、KYC 或交易流程上实测。
