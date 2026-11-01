#!/usr/bin/env python3
"""Build compact Shadowrocket configs and refresh selected public rule sources.

Standard library only. No credentials or node subscriptions are downloaded.
Network/parse failures abort before any generated file or cache is changed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import quote
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VOICE_URL = "https://openai.com/chatgpt-voice.json"
BUILTINS = {"PROXY", "DIRECT", "REJECT"}
TYPE_MAP = {"HOST": "DOMAIN", "HOST-SUFFIX": "DOMAIN-SUFFIX",
            "HOST-KEYWORD": "DOMAIN-KEYWORD", "HOST-WILDCARD": "DOMAIN-WILDCARD",
            "IP6-CIDR": "IP-CIDR"}
SIMPLE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
                "USER-AGENT", "URL-REGEX", "IP-CIDR", "IP-ASN"}
BLOCK_AI = {"googleapis.com", "google.com", "gstatic.com", "googleusercontent.com",
            "facebook.com", "fbcdn.net", "instagram.com", "x.com", "github.com",
            "amazonaws.com", "cloudfront.net", "azure.com", "blob.core.windows.net",
            "storage.googleapis.com", "livekit.cloud", "auth0.com"}


def active(text):
    return [x.strip() for x in text.splitlines()
            if x.strip() and not x.lstrip().startswith(("#", ";"))]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def validate_domain(domain):
    if (domain != domain.lower() or len(domain) > 253 or ".." in domain
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain)):
        raise ValueError(f"Invalid domain: {domain}")


def normalize(text, fmt, minimum=1):
    if "<html" in text[:300].lower() or "<!doctype" in text[:300].lower():
        raise ValueError("HTML returned instead of a rules file")
    raw = active(text)
    declared = re.search(r"^# TOTAL:\s*(\d+)", text, re.M)
    if declared and int(declared[1]) != len(raw):
        raise ValueError(f"Truncated/inconsistent source: TOTAL={declared[1]}, body={len(raw)}")
    rows = []
    for line in raw:
        if fmt == "v2fly":
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            token = line.split()[0]
            # Telemetry entries are not needed for the premium AI core.
            if "@telemetry" in line:
                continue
            if token.startswith("full:"):
                row = "DOMAIN," + token[5:]
            elif ":" in token:
                raise ValueError(f"Unsupported v2fly include/regexp; review source: {token}")
            else:
                row = "DOMAIN-SUFFIX," + token
            validate_domain(row.split(",", 1)[1])
            rows.append(row)
            continue
        parts = [x.strip() for x in line.split(",")]
        typ = TYPE_MAP.get(parts[0], parts[0])
        if typ not in SIMPLE_TYPES or len(parts) < 2:
            raise ValueError(f"Unsupported rule type: {line[:180]}")
        value = parts[1]
        if typ in {"DOMAIN", "DOMAIN-SUFFIX"}:
            validate_domain(value)
        if typ == "IP-CIDR":
            value = str(ipaddress.ip_network(value, strict=False))
        if typ == "IP-ASN" and not value.isdigit():
            raise ValueError(f"Invalid ASN: {line}")
        tail = parts[2:]
        if fmt == "quantumultx":
            # QX's third column is a policy/tag; the parent RULE-SET supplies it in SR.
            tail = [x for x in tail if x == "no-resolve"]
        elif any(x not in {"no-resolve"} for x in tail):
            raise ValueError(f"Unexpected policy in a policy-free source: {line[:180]}")
        if typ in {"IP-CIDR", "IP-ASN"}:
            tail = ["no-resolve"]
        rows.append(",".join([typ, value] + tail))
    rows = list(dict.fromkeys(rows))
    if len(rows) < minimum:
        raise ValueError(f"Unexpectedly small source: {len(rows)} < {minimum}")
    return rows


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Personal-Shadowrocket-Rule-Sync/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        body = response.read(8 * 1024 * 1024 + 1)
    if len(body) > 8 * 1024 * 1024:
        raise ValueError("Source exceeds 8 MiB")
    return body.decode("utf-8-sig")


def voice_rows(text):
    data = json.loads(text)
    prefixes = data["prefixes"]
    if not isinstance(prefixes, list) or not prefixes:
        raise ValueError("Empty OpenAI voice IP source")
    rows = []
    for item in prefixes:
        for key, value in item.items():
            if key not in {"ipv4Prefix", "ipv6Prefix"}:
                raise ValueError(f"Unknown voice address field: {key}")
            network = ipaddress.ip_network(value)
            if network.prefixlen == 0 or network.is_private or network.is_multicast:
                raise ValueError(f"Invalid voice destination: {value}")
            rows.append(f"AND,((PROTOCOL,UDP),(DST-PORT,3478),(IP-CIDR,{network}))")
    return list(dict.fromkeys(rows)), data.get("creationTime")


def rule_file(label, rows, sources=()):
    return (f"# {label}\n# Generated; edit custom/ or sources/ instead.\n"
            + "".join("# Source: " + source + "\n" for source in sources)
            + f"# TOTAL: {len(rows)}\n" + "\n".join(rows) + "\n")


def parse_sections(text):
    sections = {}; current = None
    for row in active(text):
        if row.startswith("[") and row.endswith("]"):
            current = row; sections[current] = []
        elif current:
            sections[current].append(row)
    return sections


def apply_exclusions(rows, excludes):
    excluded = set(excludes)
    return [row for row in rows if row not in excluded]


def merge_ai(upstream_rows, extras, excludes):
    dropped = []
    rows = []
    for row in list(upstream_rows) + list(extras):
        typ, domain = row.split(",", 1)
        if typ not in {"DOMAIN", "DOMAIN-SUFFIX"}:
            raise ValueError(f"AI core supports explicit domains only: {row}")
        if domain in BLOCK_AI:
            dropped.append(row)
        else:
            rows.append(row)
    return apply_exclusions(list(dict.fromkeys(rows)), excludes), sorted(set(dropped))


def compact_rules(reference, source_map, base, mirror):
    compact = []; emitted = set()
    mapping = {"AI": "rules/ai/AI.list", "VOICE": "rules/ai/AI-Voice.list",
               "AI工具下载": "rules/custom/AI-Tools.list", "Netflix": "rules/custom/Netflix-Core.list",
               "Max": "rules/custom/Max-Extra.list"}
    for row in reference:
        if row.startswith("RULE-SET,"):
            _, url, policy = row.split(",", 2)
            item = source_map[url]
            dest = base + "rules/upstream/" + item["id"] + ".list" if mirror else url
            compact.append(f"RULE-SET,{dest},{policy}")
        elif row.startswith(("GEOIP,", "FINAL,")):
            compact.append(row)
        else:
            policy = row.rsplit(",", 1)[1]
            key = "VOICE" if row.startswith("AND,") and policy == "AI" else policy
            if key not in mapping:
                raise ValueError(f"Unclassified inline rule: {row}")
            if key not in emitted:
                compact.append(f"RULE-SET,{base}{mapping[key]},{policy}")
                emitted.add(key)
    if len(compact) != 39:
        raise ValueError(f"Expected 39 compact rules; review changed template ({len(compact)})")
    return compact


def validate_config(text):
    sections = parse_sections(text)
    groups = {}
    for row in sections["[Proxy Group]"]:
        name, definition = row.split("=", 1); groups[name.strip()] = definition.strip()
    known = set(groups) | BUILTINS
    dependencies = {}
    for name, definition in groups.items():
        children = []
        for token in definition.split(",")[1:]:
            if "=" in token:
                continue
            if token not in known:
                # A named subscription is allowed only with use=true.
                if "use=true" not in definition:
                    raise ValueError(f"Unknown strategy in {name}: {token}")
            elif token in groups:
                children.append(token)
        dependencies[name] = children
    def walk(name, trail):
        if name in trail:
            raise ValueError(f"Strategy cycle: {trail + [name]}")
        for child in dependencies[name]:
            walk(child, trail + [name])
    for name in groups:
        walk(name, [])
    for row in sections["[Rule]"]:
        policy = row.split(",")[-1]
        if policy not in known:
            raise ValueError(f"Unknown rule policy: {row}")
    return {"main_rule_count": len(sections["[Rule]"]), "groups": len(groups)}


def build_outputs(root, repository, branch, texts, offline):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be OWNER/REPO")
    if not branch or any(x in branch for x in "\r\n?#"):
        raise ValueError("Invalid branch")
    base = f"https://raw.githubusercontent.com/{repository}/{quote(branch, safe='')}/"
    providers = read_json(root / "sources/upstreams.json")
    ai_sources = read_json(root / "sources/ai-upstreams.json")
    outputs = {}; source_report = {}
    for item in providers:
        text = texts[item["id"]]
        rows = normalize(text, item["format"], item["minimum_rules"])
        outputs[f"rules/upstream/{item['id']}.list"] = rule_file(item["id"], rows, [item["url"]])
        source_report[item["id"]] = {"url": item["url"], "rules": len(rows), "sha256": sha(text)}
    merged = []
    for item in ai_sources:
        text = texts[item["id"]]
        rows = normalize(text, "v2fly", item["minimum_rules"])
        merged.extend(rows)
        source_report[item["id"]] = {"url": item["url"], "rules": len(rows), "sha256": sha(text)}
    extras = normalize((root / "custom/AI-extra.list").read_text(), "shadowrocket")
    exclusions = active((root / "custom/AI-exclude.list").read_text())
    settings = read_json(root / "settings.json")
    if settings.get("include_shared_ai_hosts"):
        extras.extend(normalize((root / "custom/AI-shared-optional.list").read_text(), "shadowrocket"))
    ai, dropped = merge_ai(merged, extras, exclusions)
    if len(ai) < 100:
        raise ValueError("Unexpectedly small merged AI list")
    outputs["rules/ai/AI.list"] = rule_file("AI core", ai, [x["url"] for x in ai_sources] + ["custom/AI-extra.list"])
    voice, voice_time = voice_rows(texts["openai-voice"])
    outputs["rules/ai/AI-Voice.list"] = rule_file("ChatGPT voice UDP/3478; official creationTime=" + str(voice_time), voice, [VOICE_URL])
    source_report["openai-voice"] = {"url": VOICE_URL, "rules": len(voice), "sha256": sha(texts["openai-voice"]), "official_creation_time": voice_time}
    for name in ["AI-Tools", "Netflix-Core", "Max-Extra"]:
        rows = normalize((root / f"custom/{name}.list").read_text(), "shadowrocket")
        outputs[f"rules/custom/{name}.list"] = rule_file(name, rows, [f"custom/{name}.list"])
    network = parse_sections((root / "templates/network.conf").read_text())
    groups = (root / "templates/groups.conf").read_text()
    subscription = settings.get("ai_subscription")
    if subscription:
        if not isinstance(subscription, str) or any(c in subscription for c in ",\r\n="):
            raise ValueError("ai_subscription must be the exact simple label (no commas/newlines/equals)")
        groups = re.sub(r"^AI = .+$", f"AI = select,REJECT,{subscription},use=true,policy-regex-filter=.*,policy-select-name=REJECT", groups, flags=re.M)
    reference = read_json(root / "templates/reference_order.json")
    source_map = {x["url"]: x for x in providers}
    for mirror in [False, True]:
        rules = compact_rules(reference, source_map, base, mirror)
        header = "# Personal Shadowrocket compact config. No node credentials.\n# AI starts at REJECT; choose your premium node. Default PROXY uses Home.\n# Refresh rule sets; keep local group selections.\n"
        if repository.startswith("YOUR_"):
            header = "# SETUP REQUIRED: Run the workflow in YOUR GitHub repository before importing.\n" + header
        blocks = ["[General]\n" + "\n".join(network["[General]"]), groups.strip(), "[Rule]\n" + "\n".join(rules)]
        blocks.extend(key + "\n" + "\n".join(network[key]) for key in ["[Host]", "[URL Rewrite]", "[MITM]"])
        text = header + "\n\n".join(blocks) + "\n"
        validate_config(text)
        outputs["config/Shadowrocket-mirror.conf" if mirror else "config/Shadowrocket.conf"] = text
    report = {"repository": repository, "branch": branch, "offline_build": offline,
              "ai_domain_rules": len(ai), "voice_ip_rules": len(voice), "main_rules_per_config": 39,
              "blocked_broad_ai_rules": dropped, "sources": source_report,
              "validation_scope": "Static format and references; no live Shadowrocket engine or user node test."}
    if not offline:
        report["last_successful_fetch_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    outputs["sources/last_sync.json"] = json_text(report)
    outputs["IMPORT_URLS.txt"] = ("After successful upload + workflow, choose ONE config:\n"
                                  + base + "config/Shadowrocket.conf\n"
                                  + base + "config/Shadowrocket-mirror.conf\n")
    return outputs, report


def publish(root, outputs):
    # Everything is parsed and validated before the first write. Replacements are atomic per file.
    for rel, text in outputs.items():
        path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        fd, tmp = tempfile.mkstemp(prefix=".sync-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "YOUR_GITHUB_USERNAME/YOUR_REPOSITORY"))
    parser.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME", "main"))
    parser.add_argument("--offline", action="store_true", help="Use cached sources; no claim of a fresh fetch")
    args = parser.parse_args(argv)
    providers = read_json(ROOT / "sources/upstreams.json") + read_json(ROOT / "sources/ai-upstreams.json")
    providers.append({"id": "openai-voice", "url": VOICE_URL})
    texts = {}; failures = []
    if args.offline:
        for item in providers:
            suffix = ".json" if item["id"] == "openai-voice" else ".txt"
            texts[item["id"]] = (ROOT / "sources/cache" / (item["id"] + suffix)).read_text()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            jobs = {pool.submit(fetch, item["url"]): item for item in providers}
            for job in concurrent.futures.as_completed(jobs):
                item = jobs[job]
                try:
                    texts[item["id"]] = job.result()
                except Exception as exc:
                    failures.append(item["id"] + ": " + str(exc))
        if failures:
            raise RuntimeError("No output changed; previous published rules retained.\n" + "\n".join(failures))
    outputs, report = build_outputs(ROOT, args.repo, args.branch, texts, args.offline)
    if not args.offline:
        for item in providers:
            suffix = ".json" if item["id"] == "openai-voice" else ".txt"
            outputs["sources/cache/" + item["id"] + suffix] = texts[item["id"]]
        # Per-source current provenance supersedes the seed cache metadata.
        outputs["sources/cache-metadata.json"] = json_text(report["sources"])
    publish(ROOT, outputs)
    print(json.dumps({k: v for k, v in report.items() if k != "sources"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Sync failed; no fetched data was published: " + str(error), file=sys.stderr)
        sys.exit(1)
