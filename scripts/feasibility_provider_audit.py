"""Read-only Ollama model/template audit; makes no generate/chat calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from urllib.request import Request, urlopen

ENDPOINT = "http://127.0.0.1:11434"
TARGETS = ("qwen3.5:2b", "gemma3:4b")


def _read_json(path: str, *, body: dict[str, str] | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(ENDPOINT + path, data=data,
                      headers={"Content-Type": "application/json"} if data else {})
    with urlopen(request, timeout=5) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("Ollama metadata response must be an object")
    return value


def classify_template(template: str) -> str:
    """Conservative static classification; this is not rendered-prompt proof."""
    if '{{ .Prompt }}' in template:
        return "prompt_renderer_not_exposed_by_static_template"
    if 'eq .Role "system"' in template and '<start_of_turn>user' in template:
        return "system_messages_serialized_as_user_turns_in_static_template"
    return "role_serialization_not_verified"


def collect_audit(*, read_json=_read_json, version_reader=None) -> dict:
    if version_reader is None:
        version_reader = lambda: subprocess.check_output(
            ["ollama", "--version"], text=True, timeout=5).strip()
    models = _read_models(read_json("/api/tags"))
    output = []
    for name in TARGETS:
        tagged = models.get(name)
        if tagged is None:
            output.append({"name": name, "installed": False})
            continue
        shown = read_json("/api/show", body={"model": name})
        template = shown.get("template")
        if not isinstance(template, str) or not template:
            raise ValueError(f"No static template metadata for {name}")
        digest = tagged.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"Invalid model digest for {name}")
        output.append({
            "name": name, "installed": True, "digest": digest,
            "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
            "template_role_finding": classify_template(template),
            "rendered_prompt_status": "rendered_prompt_unverified",
            "effective_retention_status": "retention_unverifiable",
            "declared_parameters": shown.get("parameters", ""),
            "model_family": (tagged.get("details") or {}).get("family"),
            "quantization": (tagged.get("details") or {}).get("quantization_level"),
        })
    return {"ollama_version": version_reader(), "audit_kind": "read_only_metadata",
            "model_calls": 0, "models": output}


def _read_models(response: dict) -> dict[str, dict]:
    values = response.get("models")
    if not isinstance(values, list):
        raise ValueError("Ollama tag response lacks models")
    return {item["name"]: item for item in values if isinstance(item, dict)
            and isinstance(item.get("name"), str)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Optional path for redacted JSON metadata")
    args = parser.parse_args()
    audit = collect_audit()
    text = json.dumps(audit, indent=2, sort_keys=True)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
