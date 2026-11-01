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

    def test_inline_rules_from_previous_607_are_preserved_in_separate_sets(self):
        # Expanded policy-bearing custom sets must retain every previous inline matcher.
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
                self.assertIn(row, expanded)

    def test_service_specific_ai_precedes_google_twitter_and_tiktok(self):
        rows = sync.parse_sections(self.outputs["config/Shadowrocket.conf"])["[Rule]"]
        ai_index = next(i for i, row in enumerate(rows) if "/rules/ai/AI.list," in row)
        for target in ["/Google/Google.list", "/Twitter/Twitter.list", "/TikTok/TikTok.list"]:
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


if __name__ == "__main__":
    unittest.main()
