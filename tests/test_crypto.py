from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_crypto as crypto


def cached_texts():
    return {p["id"]: (ROOT / f"sources/crypto-cache/{p['id']}.txt").read_text()
            for p in crypto.common.read_json(ROOT / "sources/crypto-upstreams.json")}


class CryptoBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.report = crypto.build_outputs(ROOT, "ExampleUser/rules", "main", cached_texts(), True)

    def test_list_and_yaml_have_equal_portable_scope(self):
        plain, _ = crypto.parse_source(self.outputs["rules/crypto/Crypto.list"], "classical-text")
        yaml, _ = crypto.parse_source(self.outputs["rules/crypto/Crypto.yaml"], "classical-yaml")
        self.assertEqual(plain, yaml)
        self.assertGreater(len(plain), 250)
        self.assertTrue(all(x.split(",")[0] in crypto.DOMAIN_TYPES for x in plain))

    def test_login_api_region_wallet_and_web3_samples_and_shared_negatives(self):
        self.assertGreaterEqual(len(self.report["checks"]), 70)
        self.assertTrue(all(x["pass"] for x in self.report["checks"]))
        rows = crypto.common.active(self.outputs["rules/crypto/Crypto.list"])
        self.assertTrue(crypto.covered("zftksc.launches.appsflyersdk.com", rows))
        self.assertFalse(crypto.covered("unrelated.appsflyersdk.com", rows))
        self.assertTrue(crypto.covered("api.bybitgeorgia.ge", rows))
        self.assertFalse(crypto.covered("bybitgeorgia.ge.evil.example", rows))

    def test_known_broad_keywords_and_processes_are_reported_and_not_published(self):
        skipped = [r for s in self.report["sources"] for r in s["skipped_rules"]]
        self.assertIn("DOMAIN-KEYWORD,binance", skipped)
        self.assertIn("PROCESS-NAME,Binance.exe", skipped)
        self.assertIn("DOMAIN-SUFFIX,appsflayer.com", self.report["excluded_rules"])

    def test_html_truncation_unknown_syntax_and_policy_injection_abort(self):
        for text, fmt in [("<html>error</html>", "classical-text"),
                          ("# TOTAL: 2\nDOMAIN,example.com\n", "classical-text"),
                          ("DOMAIN,example.com,DIRECT", "classical-text"),
                          ("USER-AGENT,*Bybit*", "classical-text"),
                          ("payload:\n- DOMAIN,example.com\nproxies: []", "classical-yaml")]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                crypto.parse_source(text, fmt)

    def test_addons_keep_existing_profiles_and_use_correct_urls(self):
        self.assertNotIn("config/Shadowrocket.conf", self.outputs)
        self.assertNotIn("config/Shadowrocket-mirror.conf", self.outputs)
        self.assertIn("RULE-SET,https://raw.githubusercontent.com/ExampleUser/rules/main/rules/crypto/Crypto.list,币圈",
                      self.outputs["config/Crypto-Shadowrocket-addon.conf"])
        self.assertIn("behavior: classical", self.outputs["config/Crypto-Mihomo-addon.yaml"])
        self.assertIn("/rules/crypto/Crypto.yaml", self.outputs["config/Crypto-Mihomo-addon.yaml"])
        self.assertNotIn("MATCH,", self.outputs["config/Crypto-Mihomo-addon.yaml"])

    def test_failed_source_and_small_source_do_not_change_published_rules(self):
        dest = ROOT / "rules/crypto/Crypto.list"
        before = dest.read_bytes() if dest.exists() else None
        texts = cached_texts()
        texts["metacubex-cryptocurrency"] = "payload:\n- DOMAIN,example.com\n"
        with self.assertRaises(ValueError):
            crypto.build_outputs(ROOT, "ExampleUser/rules", "main", texts, False)
        self.assertEqual(dest.read_bytes() if dest.exists() else None, before)


if __name__ == "__main__":
    unittest.main()
