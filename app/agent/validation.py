"""Response validation. Pure functions, no I/O.

Three required guardrails (assignment Task 5):
  1. unreturned_rupee   - every ₹ figure in the answer must come from a tool result or the user
  2. approval_promise   - never promise/guarantee card approval
  3. tax_advice         - never give tax advice

Each check returns Violations; the orchestrator decides whether to only report (GUARDRAILS=off)
or enforce (GUARDRAILS=on).
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# ---------------------------------------------------------------- rupee extraction

_SUFFIX = {
    "k": 1e3, "thousand": 1e3,
    "l": 1e5, "lac": 1e5, "lacs": 1e5, "lakh": 1e5, "lakhs": 1e5, "lk": 1e5,
    "cr": 1e7, "crore": 1e7, "crores": 1e7,
}
_NUM = r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_SUF = r"(?:\s?(?:k|thousand|lakhs?|lacs?|lk|l|crores?|cr)\b)?"
_CUR = r"(?:₹|rs\.?|inr|rupees?)"

# currency-marked: "₹1,31,219.99", "Rs. 15k", "INR 2 lakh", "1.5 lakh rupees"
_CURRENCY_RE = re.compile(
    rf"{_CUR}\s?(?P<n1>{_NUM})(?P<s1>{_SUF})|(?P<n2>{_NUM})(?P<s2>{_SUF})\s?(?:rupees|inr)\b",
    re.IGNORECASE,
)
# any number, with optional suffix: used for the *allowed* set (user text, tool strings)
_ANY_NUM_RE = re.compile(rf"(?P<n>{_NUM})(?P<s>{_SUF})", re.IGNORECASE)


@dataclass(frozen=True)
class Amount:
    value: float
    tolerance: float  # how far off a source value may be and still match (display rounding)
    raw: str


def _to_amount(num: str, suffix: str, raw: str) -> Amount:
    num = num.replace(",", "")
    mult = _SUFFIX.get(suffix.strip().lower(), 1.0) if suffix else 1.0
    decimals = len(num.split(".")[1]) if "." in num else 0
    # "1.31 lakh" -> ±500 ; "15k" -> ±500 ; "₹1,31,220" -> ±1
    tol = max(0.5 * mult * 10 ** (-decimals), 1.0) if mult > 1 else 1.0
    return Amount(float(num) * mult, tol, raw.strip())


def extract_rupees(text: str) -> list[Amount]:
    """Currency-marked amounts in free text (what the answer *shows* as money)."""
    out = []
    for m in _CURRENCY_RE.finditer(text or ""):
        num, suf = (m["n1"], m["s1"]) if m["n1"] else (m["n2"], m["s2"])
        out.append(_to_amount(num, suf or "", m.group(0)))
    return out


def extract_numbers(text: str) -> list[float]:
    """Every number in text, suffix-scaled. Liberal on purpose: used to build the allowed set."""
    return [_to_amount(m["n"], m["s"] or "", m.group(0)).value for m in _ANY_NUM_RE.finditer(text or "")]


# ---------------------------------------------------------------- allowed set

def _walk_numbers(obj: Any) -> Iterable[float]:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, str):
        yield from extract_numbers(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_numbers(v)


def allowed_amounts(tool_payloads: Iterable[Any], user_messages: Iterable[str]) -> set[float]:
    """Numbers the answer may show as ₹: anything in a tool result, anything the user said,
    and monthly<->annual conversions of the user's own figures (x12, /12)."""
    allowed: set[float] = set()
    for p in tool_payloads:
        if isinstance(p, str):
            try:
                p = json.loads(p)
            except (json.JSONDecodeError, TypeError):
                pass
        allowed.update(_walk_numbers(p))
    for msg in user_messages:
        for n in extract_numbers(msg):
            allowed.update({n, n * 12, n / 12})
    return allowed


# ---------------------------------------------------------------- checks

@dataclass
class Violation:
    rule: str
    detail: str
    snippet: str


@dataclass
class ValidationReport:
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def rules(self) -> list[str]:
        return sorted({v.rule for v in self.violations})

    def as_dict(self) -> dict:
        return {"ok": self.ok, "violations": [v.__dict__ for v in self.violations]}


def check_unreturned_rupees(answer: str, allowed: set[float]) -> list[Violation]:
    out = []
    for a in extract_rupees(answer):
        if not any(abs(a.value - x) <= a.tolerance for x in allowed):
            out.append(Violation("unreturned_rupee", f"₹ figure {a.raw!r} ({a.value:g}) not in any tool result or user input", a.raw))
    return out


_NEGATION = re.compile(r"\b(not|no|never|cannot|can't|can not|isn't|is not|doesn't|don't|won't|unable|without)\b", re.I)

_APPROVAL_RE = re.compile(
    r"guarantee[sd]?\s+(?:your\s+|an?\s+)?approv\w*"
    r"|approv\w*\s+(?:is|are)\s+(?:\w+\s+)?(?:guaranteed|certain|assured|sure)"
    r"|(?:will|'ll)\s+(?:definitely|surely|certainly|easily|100%|for sure\s+)?\s*(?:be|get)\s+approved"
    r"|(?:definitely|surely|certainly)\s+(?:be|get)\s+approved"
    r"|(?:you're|you are)\s+(?:pre-?)?approved"
    r"|100\s?%\s+approv\w*"
    r"|sure[- ]shot\s+approv\w*"
    r"|instant(?:ly)?\s+approv\w*\s+guaranteed",
    re.IGNORECASE,
)


def _negated(text: str, start: int, window: int = 40) -> bool:
    return bool(_NEGATION.search(text[max(0, start - window):start]))


def check_approval_promise(answer: str) -> list[Violation]:
    out = []
    for m in _APPROVAL_RE.finditer(answer or ""):
        if _negated(answer, m.start()) or _NEGATION.search(m.group(0)):
            continue
        out.append(Violation("approval_promise", "promises or implies guaranteed approval", m.group(0)))
    return out


_TAX_RE = re.compile(
    r"\bsave\s+(?:on\s+)?(?:your\s+)?(?:income\s+)?tax(?:es)?\b"
    r"|\btax[- ](?:saving|savings|benefit|benefits|deduction|deductions|exemption|exemptions|rebate|free)\b"
    r"|\b(?:deductible|deduction)\s+under\b"
    r"|\bsection\s+80[a-z]*\b|\b80c\b|\b80d\b|\bsection\s+10\s*\("
    r"|\breduce\s+(?:your\s+)?(?:taxable\s+income|tax(?:es)?|tax\s+liability)\b"
    r"|\bclaim\s+(?:it|this|that|them|the\s+\w+(?:\s+\w+)?)\s+as\s+(?:a\s+)?(?:business\s+)?expense"
    r"|\bITR\b|\binput\s+tax\s+credit\b",
    re.IGNORECASE,
)
_DISCLAIMER = re.compile(
    r"can't|cannot|can not|not able|unable|not (?:a |qualified )?(?:tax|financial)|"
    r"don't provide|do not provide|consult|chartered accountant|\bCA\b|tax (?:advisor|adviser|professional|expert)",
    re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if s.strip()]


def _is_label(s: str, end: int) -> bool:
    """'**Tax savings:**' style heading: the match is a label, not a claim."""
    return bool(re.match(r"\s*\**\s*:", s[end:]))


def check_tax_advice(answer: str) -> list[Violation]:
    out = []
    for s in _sentences(answer):
        if _DISCLAIMER.search(s):
            continue
        hits = [m for m in _TAX_RE.finditer(s)
                if not _is_label(s, m.end()) and not _negated(s, m.start()) and not _NEGATION.search(m.group(0))]
        if hits:
            out.append(Violation("tax_advice", "gives tax guidance", s.strip()[:160]))
    return out


def validate(answer: str, tool_payloads: Iterable[Any], user_messages: Iterable[str]) -> ValidationReport:
    allowed = allowed_amounts(tool_payloads, user_messages)
    return ValidationReport(
        check_unreturned_rupees(answer, allowed)
        + check_approval_promise(answer)
        + check_tax_advice(answer)
    )
