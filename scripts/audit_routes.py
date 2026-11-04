#!/usr/bin/env python3
"""Static domain-routing samples; this is not the Shadowrocket engine."""
from pathlib import Path
import fnmatch
import json
import sync_rules as sync

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "www.youtube.com": "YouTube", "r1---sn-test.googlevideo.com": "YouTube",
    "www.netflix.com": "Netflix", "www.disneyplus.com": "Disney+",
    "www.max.com": "Max", "open.spotify.com": "Spotify",
    "telegram.org": "Telegram", "www.paypal.com": "PayPal", "x.com": "Twitter",
    "www.facebook.com": "AI", "www.amazon.com": "Amazon",
    "store.steampowered.com": "游戏平台", "github.com": "PROXY",
    "www.microsoft.com": "微软服务", "www.google.com": "谷歌服务",
    "www.apple.com": "苹果服务", "www.bilibili.com": "哔哩哔哩",
    "www.baidu.com": "DIRECT", "weixin.qq.com": "DIRECT",
    "www.xiaohongshu.com": "DIRECT", "www.douyin.com": "DIRECT",
    "www.tiktok.com": "TikTok", "oauth2.googleapis.com": "AI",
    "meta.graph.meta.com": "AI", "graph.facebook.com": "AI", "api.revenuecat.com": "AI",
    "gateway.accountscenter.meta.com": "AI", "accountscenter.meta.com": "AI",
    "auth.meta.com": "AI", "accounts.meta.com": "AI",
    "o33249.ingest.us.sentry.io": "AI",
    "webchannel-robinfrontend-pa.googleapis.com": "AI",
    "copilot.microsoft.com": "AI", "grok.x.com": "AI", "trae.ai": "AI",
    "api.github.com": "AI", "accounts.spacex.ai": "AI",
    "preview.livepreview.claude.app": "AI",
    "huggingface.co": "AI工具下载", "xethub.hf.co": "AI工具下载",
    "ollama.com": "AI工具下载",
    "anysphere-binaries.s3.us-east-1.amazonaws.com": "AI工具下载",
    "example.execute-api.us-east-1.amazonaws.com": "Amazon",
    "example.execute-api.ap-southeast-1.amazonaws.com": "Amazon",
    "example.litix.io": "PROXY", "example.brightline.tv": "PROXY",
}


def matches(host, row):
    parts = row.split(",")
    if len(parts) < 2:
        return False
    typ, value = parts[:2]
    return ((typ == "DOMAIN" and host == value) or
            (typ == "DOMAIN-SUFFIX" and (host == value or host.endswith("." + value))) or
            (typ == "DOMAIN-KEYWORD" and value in host) or
            (typ == "DOMAIN-WILDCARD" and fnmatch.fnmatchcase(host, value)))


def main():
    config = sync.parse_sections((ROOT / "config/Shadowrocket-mirror.conf").read_text())["[Rule]"]
    sets = {}
    for line in config:
        if line.startswith("RULE-SET,"):
            _, url, _ = line.split(",")
            rel = "rules/" + url.split("/rules/", 1)[1]
            sets[url] = sync.active((ROOT / rel).read_text())

    def route(host):
        for line in config:
            if line.startswith("RULE-SET,"):
                _, url, policy = line.split(",")
                if any(matches(host, row) for row in sets[url]):
                    return policy
            elif line.startswith("FINAL,"):
                return line.split(",")[1]
        return None

    checks = [{"host": host, "expected": expected, "actual": route(host),
               "pass": route(host) == expected} for host, expected in CHECKS.items()]
    report = sync.read_json(ROOT / "sources/last_sync.json")
    providers = sync.read_json(ROOT / "sources/upstreams.json")
    result = {
        "review_date": "2026-11-04",
        "scope": "Static domain matcher samples only. No DNS, IP resolution, USER-AGENT, URL, real-device or Shadowrocket-engine validation.",
        "rules_fetched_at_utc": report.get("last_successful_fetch_utc"),
        "regular_sources_checked": len(providers),
        "regular_sources": [{"id": item["id"], "policy": item["policy"],
                             "published_rules": report["sources"][item["id"]]["rules"],
                             "filtered_rules": item.get("exclude_rules", [])}
                            for item in providers],
        "checks": checks,
    }
    if any(not row["pass"] for row in checks):
        raise ValueError("Static routing regression: " + repr([r for r in checks if not r["pass"]]))
    sync.publish(ROOT, {"sources/routing-audit.json": sync.json_text(result)})
    print(json.dumps({"static_checks_passed": len(checks), "regular_sources": len(providers)}))


if __name__ == "__main__":
    main()
