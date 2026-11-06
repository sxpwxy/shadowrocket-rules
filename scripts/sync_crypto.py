#!/usr/bin/env python3
"""Build equivalent portable crypto lists without changing the user's main configs.

Only DOMAIN and DOMAIN-SUFFIX are published. Known broad keyword/process rules
are explicitly reported as skipped. Unexpected grammar aborts publication.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys

import sync_rules as common

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
SKIPPED_TYPES = {"DOMAIN-KEYWORD", "PROCESS-NAME"}
BLOCKED_ROOTS = common.BLOCK_AI | {
    "github.io", "appsflyer.com", "appsflyersdk.com", "appsflayer.com",
    "zendesk.com", "ada.support", "prismic.io", "freshchat.com",
    "geetest.com", "hcaptcha.com", "recaptcha.net", "sumsub.com",
    "crunchbase.com", "ipfs.io",
}

POSITIVE = [
    "www.bybit.com", "api.bybit.com", "stream.bybit.com", "api.bytick.com",
    "www.bybit.kz", "api.bybitgeorgia.ge", "stream.bybit.kz", "api.bybit.eu",
    "api.manepa.jp", "api.spark-fintech.com",
    "accounts.binance.com", "api.binance.com", "stream.binance.com",
    "data.binance.vision", "public.bnbstatic.com", "www.binancefuture.com",
    "www.okx.com", "openapi.okx.com", "ws.okx.com", "wspap.okx.com",
    "us.okx.com", "eea.okx.com", "www.gate.com", "api.gateio.services",
    "www.bitget.com", "www.mexc.com", "www.kucoin.com", "www.kraken.com",
    "www.coinbase.com", "www.htx.com", "www.gemini.com", "www.crypto.com",
    "metamask.io", "phantom.app", "trustwallet.com", "onekey.so",
    "safepal.com", "www.ledger.com", "trezor.io", "token.im",
    "www.tradingview.com", "widgets.tradingview-widget.com", "www.coingecko.com",
    "coinmarketcap.com", "www.coinglass.com", "defillama.com", "nansen.ai",
    "etherscan.io", "bscscan.com", "tronscan.org", "oklink.com",
    "app.uniswap.org", "app.aave.com", "pancakeswap.finance", "debank.com",
    "walletconnect.com", "redotpay.com", "www.coindesk.com",
    "sg-api.upbit.com", "rabby.io", "www.exodus.com", "pro-api.solscan.io",
    "dune.com", "api.dexscreener.com", "mempool.space",
]
NEGATIVE = [
    "chatgpt.com", "gemini.google.com", "www.youtube.com", "www.baidu.com",
    "github.com", "random.cloudfront.net", "unrelated.amazonaws.com",
    "other.appsflyersdk.com", "accounts.google.com", "challenges.cloudflare.com",
    "api.sumsub.com", "www.crunchbase.com", "ipfs.io", "www.binance.com.evil.example",
    "notbinance.example", "okx.example", "metamask.example", "unrelated.manepa.jp",
]


def parse_source(text, fmt, minimum=1):
    if "<html" in text[:300].lower() or "<!doctype" in text[:300].lower():
        raise ValueError("HTML returned instead of crypto rules")
    raw = common.active(text)
    if fmt == "classical-yaml":
        if not raw or raw[0] != "payload:":
            raise ValueError("Expected a single YAML payload list")
        raw = raw[1:]
        if any(not line.startswith("- ") for line in raw):
            raise ValueError("Unexpected YAML structure; review source")
        raw = [line[2:].strip().strip("\"'") for line in raw]
    elif fmt != "classical-text":
        raise ValueError(f"Unknown crypto source format: {fmt}")
    declared = re.search(r"^# TOTAL:\s*(\d+)", text, re.M)
    if declared and int(declared[1]) != len(raw):
        raise ValueError("Crypto source TOTAL/body mismatch")
    if len(raw) < minimum:
        raise ValueError(f"Crypto source too small: {len(raw)} < {minimum}")
    rows, skipped = [], []
    for line in raw:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 2 or not parts[1]:
            raise ValueError(f"Unexpected crypto rule or policy column: {line}")
        typ, domain = parts
        if typ in SKIPPED_TYPES:
            skipped.append(line)
        elif typ in DOMAIN_TYPES:
            common.validate_domain(domain)
            rows.append(line)
        else:
            raise ValueError(f"Unsupported crypto rule: {line}")
    return list(dict.fromkeys(rows)), skipped


def covered(host, rows):
    for row in rows:
        typ, domain = row.split(",")
        if host == domain or typ == "DOMAIN-SUFFIX" and host.endswith("." + domain):
            return True
    return False


def build_outputs(root, repository, branch, texts, offline):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be OWNER/REPO")
    providers = common.read_json(root / "sources/crypto-upstreams.json")
    rows, provenance, source_reports = [], [], []
    for provider in providers:
        body = texts[provider["id"]]
        parsed, skipped = parse_source(body, provider["format"], provider["minimum"])
        rows.extend(parsed)
        provenance.append(provider["url"])
        source_reports.append({"id": provider["id"], "url": provider["url"],
                               "sha256": common.sha(body), "domain_rules": len(parsed),
                               "skipped_rules": skipped})
    extras, skipped = parse_source((root / "custom/Crypto-extra.list").read_text(), "classical-text")
    if skipped:
        raise ValueError("Personal crypto additions must be domain rules")
    excluded = set(common.active((root / "custom/Crypto-exclude.list").read_text()))
    blocked, filtered = [], []
    for row in rows + extras:
        domain = row.split(",")[1]
        if domain in BLOCKED_ROOTS or row in excluded:
            blocked.append(row)
        else:
            filtered.append(row)
    rows = sorted(set(filtered))
    if len(rows) < 250:
        raise ValueError("Merged crypto coverage unexpectedly small")
    checks = [{"host": host, "expected": expected, "actual": covered(host, rows),
               "pass": covered(host, rows) == expected}
              for expected, hosts in [(True, POSITIVE), (False, NEGATIVE)] for host in hosts]
    if any(not item["pass"] for item in checks):
        raise ValueError("Crypto routing regression: " + repr([x for x in checks if not x["pass"]]))
    text = common.rule_file("Crypto: exchanges, wallets, market data, explorers and Web3", rows,
                            provenance + ["custom/Crypto-extra.list"])
    yaml = "\n".join(line for line in text.splitlines() if line.startswith("#")) + "\npayload:\n"
    yaml += "".join("  - " + row + "\n" for row in rows)
    # Validate the emitted YAML with the same constrained parser.
    if parse_source(yaml, "classical-yaml")[0] != rows:
        raise ValueError("Crypto YAML differs from list")
    report = {"offline_build": offline, "rules": len(rows), "sources": source_reports,
              "excluded_rules": sorted(set(blocked)), "checks": checks,
              "validation_scope": "Portable domain syntax and static samples only; no real-device, exchange login, transaction, KYC or security verification."}
    if not offline:
        report["last_successful_fetch_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    base = f"https://raw.githubusercontent.com/{repository}/{common.quote(branch, safe='')}/"
    outputs = {
        "rules/crypto/Crypto.list": text,
        "rules/crypto/Crypto.yaml": yaml,
        "sources/crypto-last-sync.json": common.json_text(report),
        "config/Crypto-Shadowrocket-addon.conf": (
            "# MERGE SNIPPET ONLY: do not activate this as a complete profile.\n"
            "# Add this group to the existing [Proxy Group], then select a node.\n"
            "[Proxy Group]\n"
            "币圈 = select,REJECT,policy-regex-filter=.*,policy-select-name=REJECT\n\n"
            "# Add BEFORE broad company/China/GEOIP/final rules in the existing [Rule].\n"
            "[Rule]\nRULE-SET," + base + "rules/crypto/Crypto.list,币圈\n"),
        "config/Crypto-Mihomo-addon.yaml": (
            "# MERGE SNIPPET ONLY: keep the existing proxy providers, groups and rules.\n"
            "# Replace the placeholder provider name with your existing provider name.\n"
            "proxy-groups:\n  - name: 币圈\n    type: select\n    use: [REPLACE_WITH_EXISTING_PROVIDER_NAME]\n"
            "rule-providers:\n  Crypto:\n    type: http\n    behavior: classical\n    format: yaml\n"
            "    interval: 86400\n    path: ./ruleset/Crypto.yaml\n    url: " + base + "rules/crypto/Crypto.yaml\n"
            "rules:\n  # Insert before broad rules and MATCH.\n  - RULE-SET,Crypto,币圈\n"),
    }
    if not offline:
        for provider in providers:
            outputs[f"sources/crypto-cache/{provider['id']}.txt"] = texts[provider["id"]]
    return outputs, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "sxpwxy/shadowrocket-rules"))
    parser.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME", "main"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    providers = common.read_json(ROOT / "sources/crypto-upstreams.json")
    if args.offline:
        texts = {p["id"]: (ROOT / f"sources/crypto-cache/{p['id']}.txt").read_text() for p in providers}
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            bodies = list(pool.map(common.fetch, [p["url"] for p in providers]))
        texts = {p["id"]: body for p, body in zip(providers, bodies)}
    outputs, report = build_outputs(ROOT, args.repo, args.branch, texts, args.offline)
    common.publish(ROOT, outputs)
    print(json.dumps({"crypto_rules": report["rules"], "sources": len(providers),
                      "static_checks": len(report["checks"]), "offline": args.offline}))


if __name__ == "__main__":
    main()
