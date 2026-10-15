"""Explicitly fetch only the seven small pinned JBB source/license files.

No model weights or target responses are downloaded. Local modified files are
never overwritten, and every download is checked against a pinned SHA-256.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

if __package__:
    from scripts.inspect_phase4_jbb import ARTIFACTS, BEHAVIORS, PINNED, ROOT
else:
    from inspect_phase4_jbb import ARTIFACTS, BEHAVIORS, PINNED, ROOT

BEHAVIOR_REVISION = "886acc352a31533ffbcf4ef22c744658688086fc"
ARTIFACT_REVISION = "909e68c01d94222b8ad2e397a017e2e12e2adb73"
LIMIT_BYTES = 1_000_000
LICENSE_SHA256 = {
    BEHAVIORS / "LICENSE": "7e1ae8f3676f39ff6e62af1743385c176a9476b1157f35bb9d05b4e6c65b7d94",
    ARTIFACTS / "LICENSE": "09017abee723a7b715866bbcd1bd2569e0a5fa7e996dd1d9d1ec4b36fb5ca51c",
}


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "SecureLLMBench-pinned-source-fetch/1"})
    with urlopen(request, timeout=30) as response:
        content = response.read(LIMIT_BYTES + 1)
    if len(content) > LIMIT_BYTES:
        raise ValueError(f"pinned source exceeds {LIMIT_BYTES} bytes")
    return content


def _path_for(tree: list[dict[str, object]], filename: str) -> str:
    matches = [str(item["path"]) for item in tree
               if item.get("type") in ("file", "blob")
               and Path(str(item.get("path", ""))).name == filename]
    if len(matches) != 1:
        raise ValueError(f"expected one upstream path for {filename}; found {len(matches)}")
    return matches[0]


def _download_verified(url: str, destination: Path, expected: str) -> str:
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
            raise FileExistsError(f"existing pinned source differs: {destination}")
        return "already_verified"
    content = _get(url)
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"upstream checksum mismatch: {destination.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(content)
    return "downloaded_and_verified"


def fetch() -> dict[str, str]:
    expected = {**PINNED, **LICENSE_SHA256}
    pending = {path: digest for path, digest in expected.items() if not path.exists()}
    if pending:
        behavior_tree_url = ("https://huggingface.co/api/datasets/JailbreakBench/JBB-Behaviors/"
                             f"tree/{BEHAVIOR_REVISION}?recursive=true")
        artifact_tree_url = ("https://api.github.com/repos/JailbreakBench/artifacts/git/trees/"
                             f"{ARTIFACT_REVISION}?recursive=1")
        behavior_tree = json.loads(_get(behavior_tree_url))
        artifact_tree = json.loads(_get(artifact_tree_url))["tree"]
    else:
        behavior_tree = artifact_tree = []
    results = {}
    for path, digest in expected.items():
        if path.parent == BEHAVIORS:
            relative = _path_for(behavior_tree, path.name) if path in pending else ""
            url = ("https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/"
                   f"{BEHAVIOR_REVISION}/{quote(relative, safe='/')}")
        else:
            relative = _path_for(artifact_tree, path.name) if path in pending else ""
            url = ("https://raw.githubusercontent.com/JailbreakBench/artifacts/"
                   f"{ARTIFACT_REVISION}/{quote(relative, safe='/')}")
        results[str(path.relative_to(ROOT))] = _download_verified(url, path, digest)
    return results


if __name__ == "__main__":
    print(json.dumps(fetch(), indent=2, sort_keys=True))
