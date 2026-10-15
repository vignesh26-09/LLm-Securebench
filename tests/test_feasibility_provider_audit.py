"""Read-only metadata audit must not infer rendered-prompt guarantees."""

import unittest

from scripts.feasibility_provider_audit import collect_audit, classify_template


class ProviderAuditTests(unittest.TestCase):
    def test_static_templates_are_not_rendered_prompt_proof(self) -> None:
        def read_json(path, *, body=None):
            if path == "/api/tags":
                return {"models": [
                    {"name": "qwen3.5:2b", "digest": "a" * 64, "details": {"family": "qwen35"}},
                    {"name": "gemma3:4b", "digest": "b" * 64, "details": {"family": "gemma3"}},
                ]}
            self.assertEqual(path, "/api/show")
            if body == {"model": "qwen3.5:2b"}:
                return {"template": "{{ .Prompt }}", "parameters": "top_p 0.95"}
            return {"template": '{{ if eq .Role "system" }}<start_of_turn>user{{ end }}',
                    "parameters": "top_p 0.95"}

        audit = collect_audit(read_json=read_json, version_reader=lambda: "ollama 0.test")
        self.assertEqual(audit["model_calls"], 0)
        self.assertEqual([row["digest"] for row in audit["models"]], ["a" * 64, "b" * 64])
        self.assertEqual(audit["models"][0]["template_role_finding"],
                         "prompt_renderer_not_exposed_by_static_template")
        self.assertEqual(audit["models"][1]["template_role_finding"],
                         "system_messages_serialized_as_user_turns_in_static_template")
        self.assertTrue(all(row["rendered_prompt_status"] == "rendered_prompt_unverified"
                            for row in audit["models"]))

    def test_missing_model_is_not_misreported_as_installed(self) -> None:
        audit = collect_audit(read_json=lambda path, **_: {"models": []},
                              version_reader=lambda: "ollama 0.test")
        self.assertTrue(all(not row["installed"] for row in audit["models"]))

    def test_unknown_template_is_unverified(self) -> None:
        self.assertEqual(classify_template("opaque renderer"), "role_serialization_not_verified")
