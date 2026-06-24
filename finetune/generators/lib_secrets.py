"""Secret-scanning and redaction for the fine-tuning dataset pipeline.

Scans text line-by-line.  For diff lines, the caller is responsible for nothing
special — `redact_diff` strips the leading +/-/space marker, scans the payload,
then re-attaches the marker so unified-diff structure is preserved.

Design goals (per the dataset spec):
  * Redact JWTs (eyJ...), sk-/sk-ant- keys, AKIA..., Bearer <token>, and
    assignments to *_SECRET / SERVICE_ROLE / API_KEY / ENC_KEY / AUTH_TOKEN /
    *_JWT_SECRET / ANON_KEY literals, plus high-entropy blobs.
  * HARVEST real infra-id literals (deployment hosts, project refs, private IPs,
    UUIDs) discovered in the repo and redact them EVERYWHERE.
  * ALLOWLIST env-reads (os.environ / process.env / _get_env / Depends) and
    obvious placeholders so we never mangle ordinary code.

Everything is deterministic: no randomness, stable ordering of substitutions.
"""

from __future__ import annotations

import math
import re
from typing import Iterable

# --------------------------------------------------------------------------- #
# Harvested infra-id literals — redacted everywhere they appear.
# These are tenant-owned deployment identifiers harvested from the repo source.
# Public third-party endpoints (CDNs, OWASP, Dubai-gov integration URLs, UAE PASS
# staging) are intentionally NOT here: they are public and load-bearing for the
# meaning of the code.  Order longest-first so substrings don't pre-empt wholes.
# --------------------------------------------------------------------------- #
HARVEST_LITERALS: list[tuple[str, str]] = [
    ("ai-smart-sourcing-dubai-chambers-production.up.railway.app", "<RAILWAY_BACKEND_HOST>"),
    ("ai-smart-sourcing-dubai-chambers.vercel.app", "<VERCEL_FRONTEND_HOST>"),
    ("smart-sourcing.devoneerstechnology.ai", "<CUSTOM_FRONTEND_DOMAIN>"),
]


def add_harvest_literal(literal: str, placeholder: str) -> None:
    """Register an additional literal to redact everywhere (dedup-safe)."""
    if not literal:
        return
    for lit, _ in HARVEST_LITERALS:
        if lit == literal:
            return
    HARVEST_LITERALS.append((literal, placeholder))
    HARVEST_LITERALS.sort(key=lambda kv: len(kv[0]), reverse=True)


# --------------------------------------------------------------------------- #
# Regex patterns.  Each entry: (name, compiled, replacement-callable-or-str).
# A replacement callable receives the match and returns the redacted text.
# --------------------------------------------------------------------------- #
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{4,}")
_JWT_BARE = re.compile(r"eyJ[A-Za-z0-9_-]{30,}")
_SK = re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9]{2,}(?:-[A-Za-z0-9]+)?[A-Za-z0-9_-]{16,}")
_AKIA = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_GH_PAT = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")
_SLACK = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")
_PRIVKEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")
_BEARER = re.compile(r"(Bearer\s+)([A-Za-z0-9._~+/=-]{12,})")
_PRIVATE_IP = re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")
_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

# Assignment of a secret-named key to a literal value (NOT an env-read).
_SECRET_KEY_NAMES = (
    r"(?:[A-Z0-9_]*SERVICE_ROLE[A-Z0-9_]*|[A-Z0-9_]*_SECRET|[A-Z0-9_]*API_KEY|"
    r"[A-Z0-9_]*ENC_KEY|[A-Z0-9_]*AUTH_TOKEN|[A-Z0-9_]*ACCESS_TOKEN|"
    r"[A-Z0-9_]*JWT_SECRET|[A-Z0-9_]*ANON_KEY|[A-Z0-9_]*PRIVATE_KEY|[A-Z0-9_]*PASSWORD|"
    r"[A-Z0-9_]*CLIENT_SECRET)"
)
# key = "literal"  /  "key": "literal"  /  key: literal
_SECRET_ASSIGN = re.compile(
    r"(?P<key>['\"]?" + _SECRET_KEY_NAMES + r"['\"]?\s*[:=]\s*)(?P<q>['\"])(?P<val>[^'\"]{6,})(?P=q)"
)

# Supabase project ref host:  <ref>.supabase.co  (ref is the tenant id)
_SUPABASE_REF = re.compile(r"\bhttps?://([a-z0-9]{20})\.supabase\.(?:co|in|net)\b")

# Contexts that mean "this is an env-read or a harmless reference", never a secret.
_ALLOW_CTX = re.compile(
    r"os\.environ|getenv|process\.env|import\.meta\.env|_get_env\s*\(|Depends\s*\(|"
    r"settings\.|config\.|Field\s*\(|examples?\s*=|description\s*=|\.env|"
    r"environ\.get|env\.str|env\.get",
    re.IGNORECASE,
)
# Values that are obviously placeholders, not real secrets.
_PLACEHOLDER_VAL = re.compile(
    r"^(?:your[_-].*|<.*>|\{\{?.*\}?\}|x{3,}|\*{3,}|changeme|placeholder|example.*|"
    r"dummy.*|test[_-].*|fake.*|redacted.*|none|null|true|false|sk-\.\.\.|\.\.\.|"
    r"\$\{?[A-Za-z_].*)$",
    re.IGNORECASE,
)


def _shannon(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _is_placeholder(val: str) -> bool:
    v = val.strip()
    if len(set(v)) <= 2:  # "aaaaaa", "------"
        return True
    return bool(_PLACEHOLDER_VAL.match(v))


# Standalone high-entropy quoted blobs (catch-all for un-named secrets).
_QUOTED = re.compile(r"(['\"])(?P<val>[A-Za-z0-9_\-+/=\.]{32,})(\1)")


def _redact_payload(text: str, hits: list[str]) -> str:
    """Redact a single logical line of text (no diff marker)."""
    allow = bool(_ALLOW_CTX.search(text))

    # 1) Harvested literals — always, regardless of allow context.
    for literal, placeholder in HARVEST_LITERALS:
        if literal in text:
            text = text.replace(literal, placeholder)
            hits.append(f"infra-literal:{literal}")

    # 2) Supabase project ref.
    def _sub_ref(m: re.Match) -> str:
        hits.append("supabase-project-ref")
        return m.group(0).replace(m.group(1), "<SUPABASE_PROJECT_REF>")

    text = _SUPABASE_REF.sub(_sub_ref, text)

    # 3) Hard token patterns — redact even inside allow context (a real JWT is a
    #    real JWT even next to the word "example"), EXCEPT obvious placeholders.
    for name, pat in (
        ("jwt", _JWT), ("jwt", _JWT_BARE), ("sk-key", _SK), ("aws-akia", _AKIA),
        ("gh-pat", _GH_PAT), ("slack-token", _SLACK), ("private-key-block", _PRIVKEY),
    ):
        def _sub(m: re.Match, _name=name) -> str:
            tok = m.group(0)
            if _is_placeholder(tok):
                return tok
            hits.append(_name)
            return f"<REDACTED_{_name.upper().replace('-', '_')}>"
        text = pat.sub(_sub, text)

    # 4) Bearer <token>
    def _sub_bearer(m: re.Match) -> str:
        if _is_placeholder(m.group(2)):
            return m.group(0)
        hits.append("bearer-token")
        return m.group(1) + "<REDACTED_TOKEN>"
    text = _BEARER.sub(_sub_bearer, text)

    # 5) Private IPs and UUIDs (infra-ids).
    def _sub_ip(m: re.Match) -> str:
        hits.append("private-ip")
        return "<PRIVATE_IP>"
    text = _PRIVATE_IP.sub(_sub_ip, text)

    def _sub_uuid(m: re.Match) -> str:
        hits.append("uuid")
        return "<UUID>"
    text = _UUID.sub(_sub_uuid, text)

    # 6) secret-named assignment to a literal — skip env-reads / placeholders.
    def _sub_assign(m: re.Match) -> str:
        val = m.group("val")
        if _is_placeholder(val) or _ALLOW_CTX.search(m.group(0)):
            return m.group(0)
        hits.append("secret-assignment")
        return f"{m.group('key')}{m.group('q')}<REDACTED_SECRET>{m.group('q')}"
    text = _SECRET_ASSIGN.sub(_sub_assign, text)

    # 7) High-entropy quoted blob catch-all (skip allow context + placeholders).
    if not allow:
        def _sub_blob(m: re.Match) -> str:
            val = m.group("val")
            if _is_placeholder(val):
                return m.group(0)
            # Skip things that look like file paths or dotted identifiers.
            if "/" in val or (val.count(".") >= 2 and "=" not in val):
                return m.group(0)
            if _shannon(val) >= 4.0 and len(val) >= 32:
                hits.append("high-entropy-blob")
                q = m.group(1)
                return f"{q}<REDACTED_HIGH_ENTROPY>{q}"
            return m.group(0)
        text = _QUOTED.sub(_sub_blob, text)

    return text


def redact_line(line: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    return _redact_payload(line, hits), hits


def redact_text(text: str) -> tuple[str, list[str]]:
    """Redact arbitrary multi-line text (e.g. an instruction)."""
    hits: list[str] = []
    out = [_redact_payload(ln, hits) for ln in text.split("\n")]
    return "\n".join(out), hits


def redact_diff(diff: str) -> tuple[str, list[str]]:
    """Redact a unified diff, preserving +/-/space markers and headers."""
    hits: list[str] = []
    out_lines: list[str] = []
    for ln in diff.split("\n"):
        if ln[:4] in ("--- ", "+++ ") or ln.startswith("@@") or ln.startswith("diff ") \
                or ln.startswith("index ") or ln.startswith("new file") \
                or ln.startswith("deleted file") or ln.startswith("rename ") \
                or ln.startswith("similarity ") or ln.startswith("Binary "):
            # Headers: still redact harvested infra literals + supabase refs in
            # the path (rare) but keep structure.
            red = ln
            for literal, placeholder in HARVEST_LITERALS:
                if literal in red:
                    red = red.replace(literal, placeholder)
                    hits.append(f"infra-literal:{literal}")
            out_lines.append(red)
            continue
        marker, payload = (ln[:1], ln[1:]) if ln[:1] in ("+", "-", " ") else ("", ln)
        red_payload, line_hits = redact_line(payload)
        hits.extend(line_hits)
        out_lines.append(marker + red_payload)
    return "\n".join(out_lines), hits


def scan_text(text: str) -> list[str]:
    """Return the list of secret-types found WITHOUT mutating (for validation)."""
    _, hits = redact_text(text)
    return hits


def scan_strings(texts: Iterable[str]) -> dict[str, int]:
    """Aggregate scan over many strings -> {secret_type: count}."""
    agg: dict[str, int] = {}
    for t in texts:
        for h in scan_text(t):
            key = h.split(":", 1)[0]
            agg[key] = agg.get(key, 0) + 1
    return agg


if __name__ == "__main__":
    # Self-test with synthetic secrets (NOT real).
    samples = [
        '+    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiUzI1NiIsInR5cCI6IkpXVCJ9.fakefakefake.signaturesig"',
        '+    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # env-read, keep',
        '+    api_key = "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"',
        '+    headers = {"Authorization": "Bearer abc123def456ghi789xyz"}',
        '+    url = "https://ai-smart-sourcing-dubai-chambers.vercel.app/api"',
        '+    PLACEHOLDER = "your-api-key-here"',
        ' context line referencing https://owasp.org should stay',
        '+    host = "10.0.12.34"',
    ]
    for s in samples:
        red, hits = redact_diff(s)
        print(f"{hits!s:45} {red}")
