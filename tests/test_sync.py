import importlib.util
import ipaddress
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_rules", ROOT / "scripts/sync_rules.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def texts():
    result = {}
    for item in sync.read_json(ROOT / "sources/upstreams.json") + sync.read_json(ROOT / "sources/ai-upstreams.json"):
        result[item["id"]] = (ROOT / "sources/cache" / (item["id"] + ".txt")).read_text()
    result["openai-voice"] = (ROOT / "sources/cache/openai-voice.json").read_text()
    return result


class RuleBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.report = sync.build_outputs(ROOT, "ExampleUser/personal-rules", "main", texts(), True)

    def test_both_configs_have_39_rules_and_distinct_update_paths(self):
        for name in ["config/Shadowrocket.conf", "config/Shadowrocket-mirror.conf"]:
            self.assertEqual(sync.validate_config(self.outputs[name])["main_rule_count"], 39)
        hybrid = sync.parse_sections(self.outputs["config/Shadowrocket.conf"])["[Rule]"]
        mirror = sync.parse_sections(self.outputs["config/Shadowrocket-mirror.conf"])["[Rule]"]
        self.assertTrue(any("raw.githubusercontent.com/blackmatrix7/" in row for row in hybrid))
        self.assertTrue(all("raw.githubusercontent.com/ExampleUser/personal-rules/main/" in row
                            for row in mirror if row.startswith("RULE-SET,")))

    def test_previous_inline_rules_preserved_except_reviewed_shared_video_hosts(self):
        # Retain old inline matchers except two explicitly reviewed shared video hosts.
        removed = {"DOMAIN-SUFFIX,litix.io,Max", "DOMAIN-SUFFIX,brightline.tv,Max"}
        expanded = set()
        policy_for = {"AI.list": "AI", "AI-Voice.list": "AI", "AI-Tools.list": "AI工具下载",
                      "Netflix-Core.list": "Netflix", "Max-Extra.list": "Max"}
        for path, text in self.outputs.items():
            if path.startswith(("rules/ai/", "rules/custom/")):
                policy = policy_for[Path(path).name]
                for row in sync.active(text):
                    expanded.add(row + "," + policy)
        reference = sync.read_json(ROOT / "templates/reference_order.json")
        for row in reference:
            if not row.startswith(("RULE-SET,", "GEOIP,", "FINAL,")):
                if row in removed:
                    self.assertNotIn(row, expanded)
                else:
                    self.assertIn(row, expanded)

    def test_service_specific_ai_precedes_google_twitter_and_tiktok(self):
        rows = sync.parse_sections(self.outputs["config/Shadowrocket.conf"])["[Rule]"]
        ai_index = next(i for i, row in enumerate(rows) if "/rules/ai/AI.list," in row)
        for target in ["/Google/Google.list", "/Twitter/Twitter.list", "/TikTok/TikTok.list",
                       "/Facebook/Facebook.list", "/Microsoft/Microsoft.list", "/QuantumultX/Apple/Apple.list"]:
            self.assertLess(ai_index, next(i for i, row in enumerate(rows) if target in row))

    def test_public_shared_suffixes_are_not_accepted_into_ai(self):
        rows, dropped = sync.merge_ai(["DOMAIN-SUFFIX,googleapis.com", "DOMAIN,gemini.google.com",
                                       "DOMAIN-SUFFIX,livekit.cloud"], ["DOMAIN-SUFFIX,muse.ai"], [])
        self.assertIn("DOMAIN,gemini.google.com", rows)
        self.assertIn("DOMAIN-SUFFIX,muse.ai", rows)
        self.assertEqual(len(dropped), 2)

    def test_custom_additions_and_removals_survive_upstream_merge(self):
        rows, _ = sync.merge_ai(["DOMAIN-SUFFIX,example.ai", "DOMAIN,old.example.ai"],
                                 ["DOMAIN,my-api.example.net"], ["DOMAIN,old.example.ai"])
        self.assertIn("DOMAIN,my-api.example.net", rows)
        self.assertNotIn("DOMAIN,old.example.ai", rows)

    def test_voice_rules_are_all_limited_to_udp_3478(self):
        voice = sync.active(self.outputs["rules/ai/AI-Voice.list"])
        self.assertGreater(len(voice), 100)
        for row in voice:
            self.assertTrue(row.startswith("AND,((PROTOCOL,UDP),(DST-PORT,3478),(IP-CIDR,"))
            ipaddress.ip_network(row.split("(IP-CIDR,", 1)[1].split(")", 1)[0])

    def test_qx_tags_removed_and_ipv6_converted(self):
        rows = sync.normalize("HOST-SUFFIX,example.com,Service\nIP6-CIDR,2001:db8::/32,Service\n", "quantumultx")
        self.assertEqual(rows, ["DOMAIN-SUFFIX,example.com", "IP-CIDR,2001:db8::/32,no-resolve"])

    def test_truncated_source_html_and_policy_injection_rejected(self):
        for content in ["# TOTAL: 2\nDOMAIN,example.com\n", "<!DOCTYPE html><html>Error</html>",
                        "DOMAIN,example.com,DIRECT"]:
            with self.assertRaises(ValueError):
                sync.normalize(content, "shadowrocket")

    def test_failed_build_cannot_modify_published_output(self):
        bad = texts(); bad["Google"] = "<!DOCTYPE html><html>error</html>"
        sentinel = ROOT / "config/Shadowrocket.conf"
        before = sentinel.read_bytes() if sentinel.exists() else None
        with self.assertRaises(ValueError):
            sync.build_outputs(ROOT, "ExampleUser/personal-rules", "main", bad, False)
        self.assertEqual(before, sentinel.read_bytes() if sentinel.exists() else None)

    def test_base_network_settings_unchanged(self):
        original = sync.parse_sections((ROOT / "templates/network.conf").read_text())
        built = sync.parse_sections(self.outputs["config/Shadowrocket.conf"])
        for key in ["[General]", "[Host]", "[URL Rewrite]", "[MITM]"]:
            self.assertEqual(original[key], built[key])

    def test_repeat_build_is_deterministic(self):
        again, _ = sync.build_outputs(ROOT, "ExampleUser/personal-rules", "main", texts(), True)
        self.assertEqual(self.outputs, again)

    def test_invalid_repository_and_new_source_grammar_do_not_get_published(self):
        with self.assertRaises(ValueError):
            sync.build_outputs(ROOT, "bad/repo/extra", "main", texts(), True)
        with self.assertRaises(ValueError):
            sync.normalize("include:unreviewed-file\n", "v2fly")


    def test_observed_session_hosts_and_new_signin_hosts_route_to_ai(self):
        rows = sync.active(self.outputs["rules/ai/AI.list"])
        def covered(host):
            return any((parts[0] == "DOMAIN" and host == parts[1]) or
                       (parts[0] == "DOMAIN-SUFFIX" and
                        (host == parts[1] or host.endswith("." + parts[1])))
                       for parts in (row.split(",") for row in rows))
        # Shared authentication, mobile diagnostics, and the sibling WebChannel host
        # previously escaped to Google/Facebook/FINAL despite AI core traffic matching.
        for host in ["oauth2.googleapis.com", "oauthaccountmanager.googleapis.com",
                     "signaler-pa.googleapis.com", "accounts.google.com",
                     "webchannel-robinfrontend-pa.googleapis.com",
                     "gateway.accountscenter.meta.com", "accountscenter.meta.com",
                     "auth.meta.com", "accounts.meta.com",
                     "meta.graph.meta.com", "ar.graph.meta.com", "graph.facebook.com", "shortwave.facebook.com", "www.facebook.com",
                     "api.revenuecat.com", "o33249.ingest.us.sentry.io",
                     "accounts.spacex.ai", "auth.grokusercontent.com",
                     "api.github.com", "bridge.claudeusercontent.com",
                     "preview.livepreview.claude.app"]:
            with self.subTest(host=host):
                self.assertTrue(covered(host))
        for host in ["other.googleapis.com", "other.graph.meta.com",
                     "accountscenter.meta.com.example.org", "unrelated.meta.com",
                     "media.auth.meta.com", "video.cdninstagram.com",
                     "other.ingest.us.sentry.io", "other.revenuecat.com",
                     "m.facebook.com", "video.facebook.com", "www.apple.com", "github.com",
                     "unrelated.amazonaws.com"]:
            with self.subTest(unrelated_host=host):
                self.assertFalse(covered(host))

    def test_video_sources_do_not_capture_shared_regional_api_gateways(self):
        hybrid = sync.parse_sections(self.outputs["config/Shadowrocket.conf"])["[Rule]"]
        for service in ["Disney", "HBO"]:
            published = self.outputs[f"rules/upstream/{service}.list"]
            self.assertNotIn("DOMAIN-SUFFIX,execute-api.", published)
            # Even hybrid mode must use this filtered copy, not bypass the correction.
            self.assertTrue(any(f"ExampleUser/personal-rules/main/rules/upstream/{service}.list" in r for r in hybrid))
        max_rules = sync.active(self.outputs["rules/custom/Max-Extra.list"])
        self.assertEqual(max_rules, ["DOMAIN-SUFFIX,discomax.com"])

    def test_ai_model_downloads_and_voice_remain_separate(self):
        rows = sync.active(self.outputs["rules/ai/AI.list"])
        self.assertNotIn("DOMAIN-SUFFIX,huggingface.co", rows)
        self.assertNotIn("DOMAIN-SUFFIX,ollama.com", rows)
        tools = sync.active(self.outputs["rules/custom/AI-Tools.list"])
        self.assertIn("DOMAIN,anysphere-binaries.s3.us-east-1.amazonaws.com", tools)
        # Broad provider roots must never be introduced by an upstream or custom list.
        for domain in ["meta.com", "googleapis.com", "sentry.io", "revenuecat.com",
                       "apple.com", "cloudflare.com", "amazonaws.com"]:
            _, rejected = sync.merge_ai(["DOMAIN-SUFFIX," + domain], [], [])
            self.assertEqual(rejected, ["DOMAIN-SUFFIX," + domain])


if __name__ == "__main__":
    unittest.main()
