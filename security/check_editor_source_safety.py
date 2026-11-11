"""Fail-closed, dependency-free source check for editor autostart and font assets.

This reads source only. It NEVER runs tasks, scripts, or any font contents.
Passing does not establish workstation or deployed runtime cleanliness.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

# Font assets from ROOTS signed clean PR #14 merge 2de3b048; .gitignore is a new local policy.
# Normalize CRLF to LF for SVG ONLY: Windows Git checkout may change text lines.
FONT_SHA256 = {
    "README.md": "fdcbe2fe72dc508fd189c73352185da33acb44792e0db696705ec368503456b1",
    "fa-brands-400.eot": "811e1577184066108ceca86d5a624a9012303df5206c5cb0b27d5e3fedcba5a3",
    "fa-brands-400.svg": "02340ba1789d09bcc507563c89c4a847ba537bb8132082777a50519cf74bcb5b",
    "fa-brands-400.ttf": "a0c145382acfe59767d1487d6505f349665b685c2885cd91b621d141a292b0f8",
    "fa-brands-400.woff": "e836c5d5dfc13e18170c5bddefb4fdac7c65ac0ad43a4b431acdc4a98865a260",
    "fa-brands-400.woff2": "5d9190292acdd48ba0fc35080f7e7448f3cdf0d79199a4d23f0f49b5341fdf29",
    "fa-regular-400.eot": "01f4416f5db59e2dd6b6fbd9dc32336d99db18f7eb623a49f584d04afd279473",
    "fa-regular-400.svg": "865fd23de13b1920280e182359579e09eff7a09eb24676eceec7552838559f55",
    "fa-regular-400.ttf": "f32b94a29060dfec0c797a1dfe111357eb1d682f1aca4ac4b95cf0f4c3e2bfa9",
    "fa-regular-400.woff": "8e2d96198711b63752e5f2f5987b8ffc536df6156a065bdbe28cb7231cad793d",
    "fa-regular-400.woff2": "6a8c8e9e1e7f692c21af1956de163f3d026778e6449fe93a09a671847ca1ae65",
    "fa-solid-900.eot": "32501727bb23fc77615b1ec76b5f298ec22198c0f3d6a3e7d6fe4ac3cf315db9",
    "fa-solid-900.svg": "e768539808757f7eec20f09c9ee9b36b0e6c5636e90c9ee697995cbbc6ee0555",
    "fa-solid-900.ttf": "231d68cefbc6846fb78cafca8467401a4f371e226418662e8900e3d52adc00ab",
    "fa-solid-900.woff": "352f8ead280419dd953d2bc7843386bb9430e8152c2dbd2c2d2494f6b9567ee7",
    "fa-solid-900.woff2": "7f4d3fd0a705dbf8403298aad91d5de6972e6b5d536068eba8b24954a5a0a8c7",
}

# A changed ignore file can hide future malicious editor/font content.
# ROOTS had no .gitignore at signed clean merge 2de3b048; this digest pins
# the new explicit source-only secret-output policy introduced by this patch.
TRUSTED_IGNORE_SHA256 = "4213fa203bb10449ea543625f73b7e5670f0f1ff9fe6092b0dee710d851268c0"


def _without_jsonc_comments(text: str) -> str:
    """Blank JSONC comments and trailing commas without touching string literals."""
    chars = list(text)
    pos = 0
    quoted = False
    while pos < len(chars):
        current = chars[pos]
        if quoted:
            if current == "\\":
                pos += 2
                continue
            if current == '"':
                quoted = False
            pos += 1
            continue
        if current == '"':
            quoted = True
            pos += 1
            continue
        if current == "/" and pos + 1 < len(chars) and chars[pos + 1] == "/":
            end = pos
            while end < len(chars) and chars[end] not in "\r\n":
                chars[end] = " "
                end += 1
            pos = end
            continue
        if current == "/" and pos + 1 < len(chars) and chars[pos + 1] == "*":
            end = pos + 2
            while end + 1 < len(chars) and not (chars[end] == "*" and chars[end + 1] == "/"):
                end += 1
            if end + 1 >= len(chars):
                raise ValueError("unclosed JSONC block comment")
            for idx in range(pos, end + 2):
                if chars[idx] not in "\r\n":
                    chars[idx] = " "
            pos = end + 2
            continue
        pos += 1

    pos = 0
    quoted = False
    while pos < len(chars):
        current = chars[pos]
        if quoted:
            if current == "\\":
                pos += 2
                continue
            if current == '"':
                quoted = False
            pos += 1
            continue
        if current == '"':
            quoted = True
        elif current == ",":
            look = pos + 1
            while look < len(chars) and chars[look].isspace():
                look += 1
            if look < len(chars) and chars[look] in "}]":
                # A comma immediately after an opener (or another comma) is
                # malformed JSON, not an optional trailing comma.
                prior = pos - 1
                while prior >= 0 and chars[prior].isspace():
                    prior -= 1
                if prior >= 0 and chars[prior] not in "{[,:":
                    chars[pos] = " "
        pos += 1
    return "".join(chars)


def parse_jsonc(raw: bytes) -> object:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSONC key: {key}")
            result[key] = value
        return result

    text = raw.decode("utf-8-sig")
    return json.loads(_without_jsonc_comments(text), object_pairs_hook=unique_pairs)


def _walk(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def check_tree(root: Path) -> list[str]:
    issues: list[str] = []
    vscode = root / ".vscode"
    fonts = root / "public" / "fonts"
    if not vscode.is_dir() or vscode.is_symlink():
        issues.append("missing or symlinked .vscode directory")
    if not fonts.is_dir() or fonts.is_symlink():
        issues.append("missing or symlinked public/fonts directory")

    editor_files: set[Path] = set()
    # A multi-root VS Code workspace may open nested projects. Case-insensitive
    # Windows checkouts may recognize `.VSCODE` and `TASKS.JSON` too, despite
    # Linux CI globbing being case-sensitive.
    for path in root.rglob("*"):
        if path.name.lower().endswith(".code-workspace"):
            editor_files.add(path)
        if path.name.lower() != ".vscode":
            continue
        if path.name != ".vscode":
            issues.append(f"case-variant editor directory: {path.relative_to(root)}")
        if path.is_symlink() or not path.is_dir():
            issues.append(f"symlinked/non-directory editor path: {path.relative_to(root)}")
            continue
        for config in path.rglob("*"):
            if config.is_symlink():
                issues.append(f"symlinked editor path: {config.relative_to(root)}")
            elif config.is_file() and config.suffix.lower() in {".json", ".jsonc"}:
                editor_files.add(config)
    for expected in (vscode / "tasks.json", vscode / "settings.json"):
        if not expected.is_file() or expected.is_symlink():
            issues.append(f"missing or symlinked editor configuration: {expected.relative_to(root)}")

    for path in sorted(editor_files):
        if path.is_symlink():
            issues.append(f"symlinked workspace: {path.relative_to(root)}")
            continue
        if path.name.lower() in {"tasks.json", "settings.json"} and path.name not in {"tasks.json", "settings.json"}:
            issues.append(f"case-variant editor file: {path.relative_to(root)}")
        try:
            payload = parse_jsonc(path.read_bytes())
        except (OSError, UnicodeError, ValueError) as exc:
            issues.append(f"invalid editor JSONC {path.relative_to(root)}: {exc}")
            continue
        if not isinstance(payload, dict):
            issues.append(f"editor configuration is not an object: {path.relative_to(root)}")
            continue
        location = str(path.relative_to(root))
        for node in _walk(payload):
            options = node.get("runOptions")
            if node.get("runOn") == "folderOpen" or (isinstance(options, dict) and options.get("runOn") == "folderOpen"):
                issues.append(f"folderOpen editor execution: {location}")
            if "task.allowAutomaticTasks" in node and node["task.allowAutomaticTasks"] != "off":
                issues.append(f"automatic editor tasks enabled: {location}")
        # Any font path in editor tasks is suspicious; runtime assets are never commands.
        if "public/fonts/" in " ".join(_strings(payload)).lower().replace("\\", "/"):
            issues.append(f"font referenced by editor configuration: {location}")
        if path.name.lower() == "settings.json" and "tasks" in payload:
            issues.append(f"embedded tasks in editor settings: {location}")

    if fonts.is_dir() and not fonts.is_symlink():
        found = set()
        for path in fonts.iterdir():
            found.add(path.name)
            if path.is_symlink() or not path.is_file():
                issues.append(f"symlink/non-file font asset: {path.relative_to(root)}")
                continue
            expected = FONT_SHA256.get(path.name)
            if expected is None:
                issues.append(f"unapproved font asset: {path.relative_to(root)}")
                continue
            content = path.read_bytes()
            if path.suffix.lower() == ".svg" or path.name == "README.md":
                # Legitimate text assets may be checked out CRLF on Windows;
                # only newline style changes are ignored, not content changes.
                content = content.replace(b"\r\n", b"\n")
            if hashlib.sha256(content).hexdigest() != expected:
                issues.append(f"font asset hash mismatch: {path.relative_to(root)}")
        for name in FONT_SHA256.keys() - found:
            issues.append(f"missing approved font asset: public/fonts/{name}")

    ignore = root / ".gitignore"
    if not ignore.is_file() or ignore.is_symlink():
        issues.append("missing or symlinked .gitignore")
    else:
        ignore_bytes = ignore.read_bytes()
        if hashlib.sha256(ignore_bytes).hexdigest() != TRUSTED_IGNORE_SHA256:
            issues.append(".gitignore differs from the explicit new ROOTS safe policy")
        lines = [line.strip() for line in ignore_bytes.decode("utf-8").splitlines()]
        if ".env" not in lines:
            issues.append(".gitignore missing .env")
        normalized = [entry.removeprefix("./").rstrip("/").casefold() for entry in lines]
        for forbidden in ("config.bat", "node_modules", ".vscode", "public/fonts"):
            if forbidden in normalized:
                issues.append(f"suspicious newly ignored path: {forbidden}")
    return issues


def main() -> int:
    issues = check_tree(ROOT)
    for issue in issues:
        print(f"FAIL: {issue}", file=sys.stderr)
    if issues:
        return 1
    print("ROOTS editor source and font provenance: PASS (source only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
