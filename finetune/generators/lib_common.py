"""Shared library: schema serializers, tokenizer, near-dup (MinHash), validators.

Target platforms (dual emit):
  * anthropic  -> {"system": "...", "messages":[{user},{assistant}]}
  * axolotl    -> {"messages":[{system},{user},{assistant}]}  (chat_template)

Tokenizer: tiktoken o200k_base is the universal measuring stick.  Anthropic has
no offline tokenizer (API-only) so its sizes are this approximation, clearly
labeled.  For axolotl an HF base tokenizer is attempted in lib_tokenizers;
otherwise the same approximation is used.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

import tiktoken

# One consistent system message across the whole dataset.
SYSTEM_MESSAGE = (
    "You are a senior software engineer working in the Dubai Chambers "
    "\"AI Smart Sourcing\" codebase: a FastAPI + Supabase/Postgres backend "
    "(service-oriented, Pydantic v2, tables prefixed chamber_) and a React 18 + "
    "Vite + Tailwind frontend (.jsx). Follow the repository's existing "
    "conventions. Respond with only the requested code artifact inside a single "
    "fenced code block and no prose outside it."
)

_FENCE = {"python": "python", "jsx": "jsx", "javascript": "javascript",
          "typescript": "tsx", "tsx": "tsx", "sql": "sql", "css": "css",
          "yaml": "yaml", "bash": "bash", "json": "json"}

_ENC = tiktoken.get_encoding("o200k_base")


def count_tokens(text: str) -> int:
    return len(_ENC.encode(text, disallowed_special=()))


# --------------------------------------------------------------------------- #
# Output-form suffix + assistant fenced block
# --------------------------------------------------------------------------- #
def instruction_with_suffix(instruction: str, *, source: str, kind: str, file: str) -> str:
    instr = instruction.strip()
    if source == "real":
        if kind == "new-file":
            suffix = f"Provide your answer as a unified diff that creates `{file}`."
        else:
            suffix = f"Provide your answer as a unified diff for `{file}`."
    else:  # synthetic -> complete file
        suffix = f"Provide the complete contents of `{file}`."
    # avoid double-naming if the instruction already ends with the file mention
    return f"{instr} {suffix}"


def assistant_block(output: str, *, source: str, lang: str) -> str:
    body = output.rstrip("\n")
    if source == "real":
        return f"```diff\n{body}\n```"
    fence = _FENCE.get(lang, "")
    return f"```{fence}\n{body}\n```"


# --------------------------------------------------------------------------- #
# Schema serializers
# --------------------------------------------------------------------------- #
def to_anthropic(user: str, assistant: str) -> dict:
    return {"system": SYSTEM_MESSAGE,
            "messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}


def to_axolotl(user: str, assistant: str) -> dict:
    return {"messages": [{"role": "system", "content": SYSTEM_MESSAGE},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}


def dumps_ascii(obj: dict) -> str:
    """One compact JSON line, pure ASCII, no trailing whitespace."""
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# Exact + near-duplicate detection (token-shingle MinHash + LSH)
# --------------------------------------------------------------------------- #
_WS = re.compile(r"\s+")
_TOK = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]")


def normalize_for_hash(text: str) -> str:
    return _WS.sub(" ", text.strip()).lower()


def exact_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode()).hexdigest()


def _shingles(text: str, k: int = 5) -> set[int]:
    toks = _TOK.findall(text.lower())
    if len(toks) < k:
        grams = {" ".join(toks)} if toks else set()
    else:
        grams = {" ".join(toks[i:i + k]) for i in range(len(toks) - k + 1)}
    return {int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big") for g in grams}


_MERSENNE = (1 << 61) - 1
# Deterministic permutation coefficients (fixed seed -> fixed a,b).
_NUM_PERM = 128
_rng_state = 0x9E3779B97F4A7C15


def _det_rand() -> int:
    global _rng_state
    _rng_state = (_rng_state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    return _rng_state


_PERMS = [( (_det_rand() % (_MERSENNE - 1)) + 1, _det_rand() % _MERSENNE) for _ in range(_NUM_PERM)]


def minhash_signature(text: str) -> tuple[int, ...]:
    sh = _shingles(text)
    if not sh:
        return tuple([0] * _NUM_PERM)
    sig = []
    for a, b in _PERMS:
        sig.append(min(((a * x + b) % _MERSENNE) for x in sh))
    return tuple(sig)


def estimated_jaccard(sig_a: tuple[int, ...], sig_b: tuple[int, ...]) -> float:
    if not sig_a or not sig_b:
        return 0.0
    return sum(1 for x, y in zip(sig_a, sig_b) if x == y) / len(sig_a)


def near_dup_pairs(signatures: list[tuple[int, tuple[int, ...]]], threshold: float = 0.9,
                   bands: int = 32) -> list[tuple[int, int]]:
    """LSH-banded candidate generation -> verify by estimated Jaccard.

    signatures: list of (key, signature).  Returns key pairs that are near-dups.
    """
    rows = _NUM_PERM // bands
    buckets: dict[tuple, list[int]] = {}
    for idx, (_key, sig) in enumerate(signatures):
        for b in range(bands):
            band = (b,) + tuple(sig[b * rows:(b + 1) * rows])
            buckets.setdefault(band, []).append(idx)
    seen: set[tuple[int, int]] = set()
    dups: list[tuple[int, int]] = []
    for members in buckets.values():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                if estimated_jaccard(signatures[a][1], signatures[b][1]) >= threshold:
                    dups.append((signatures[a][0], signatures[b][0]))
    return dups


# --------------------------------------------------------------------------- #
# Strict record validation (independent of jq; jq runs too in build)
# --------------------------------------------------------------------------- #
def validate_line(line: str, *, schema: str, max_tokens: int = 16000) -> list[str]:
    issues = []
    if line.endswith("\n"):
        issues.append("line includes trailing newline in payload")
    if "﻿" in line:
        issues.append("contains BOM")
    try:
        line.encode("ascii")
    except UnicodeEncodeError:
        issues.append("non-ASCII byte present")
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as e:
        return issues + [f"invalid JSON: {e}"]
    msgs = obj.get("messages")
    if not isinstance(msgs, list) or not msgs:
        issues.append("missing/empty messages[]")
        return issues
    if schema == "anthropic":
        if not isinstance(obj.get("system"), str) or not obj["system"].strip():
            issues.append("anthropic: missing system")
        roles = [m.get("role") for m in msgs]
        if roles != ["user", "assistant"]:
            issues.append(f"anthropic: roles must be [user,assistant], got {roles}")
    else:  # axolotl
        roles = [m.get("role") for m in msgs]
        if roles != ["system", "user", "assistant"]:
            issues.append(f"axolotl: roles must be [system,user,assistant], got {roles}")
    for m in msgs:
        if not isinstance(m.get("content"), str) or not m["content"].strip():
            issues.append(f"empty content for role {m.get('role')}")
    full = " ".join(m.get("content", "") for m in msgs) + obj.get("system", "")
    if count_tokens(full) > max_tokens:
        issues.append(f"exceeds {max_tokens} tokens")
    return issues


def iter_jsonl(path: str) -> Iterable[str]:
    with open(path, "rb") as f:
        for raw in f:
            yield raw.decode("utf-8").rstrip("\n")
