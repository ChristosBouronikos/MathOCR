"""LaTeX text utilities for MathOCR.

Authored by Bouronikos Christos <chrisbouronikos@gmail.com>.
Donations are welcome at https://paypal.me/christosbouronikos.

These helpers are deliberately dependency-free so the recognition quality
logic (normalization, similarity, and sanity scoring used by the engine
ensemble) can be unit-tested without downloading any model weights.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_DELIMITER_PAIRS = (("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$"))

# Commands that change spacing or sizing but never the mathematical meaning.
# They are removed before two engine outputs are compared for agreement. The
# punctuation forms (\, \; \: \!) need their own alternative because \b never
# matches between two non-word characters.
_COSMETIC_COMMANDS = re.compile(
    r"\\(?:left|right|quad|qquad|limits|nolimits|displaystyle|textstyle"
    r"|scriptstyle|scriptscriptstyle|thinspace|medspace|thickspace|big|Big|bigg|Bigg"
    r"|bigl|bigr|Bigl|Bigr|biggl|biggr|Biggl|Biggr|mathstrut|allowbreak)\b"
    r"|\\[,;:!]"
)

_TOKEN_PATTERN = re.compile(r"\\[A-Za-z]+|\\.|[^\s\\]")


def clean_latex(value: str) -> str:
    """Remove transport delimiters while retaining the mathematical expression."""

    cleaned = value.strip()
    for prefix, suffix in _DELIMITER_PAIRS:
        wrapped = cleaned.startswith(prefix) and cleaned.endswith(suffix)
        if wrapped and len(cleaned) > len(prefix) + len(suffix):
            cleaned = cleaned[len(prefix) : -len(suffix)].strip()
            break
    return cleaned


def tokenize(latex: str) -> list[str]:
    """Split LaTeX into commands and single characters, ignoring whitespace."""

    return _TOKEN_PATTERN.findall(latex)


def normalize_for_comparison(latex: str) -> str:
    """Reduce a LaTeX string to a canonical form for cross-engine agreement.

    Different engines legitimately disagree about spacing commands, fraction
    style, and brace placement around single tokens. Removing that variation
    keeps the ensemble vote about mathematical content rather than style.
    """

    value = clean_latex(latex)
    value = _COSMETIC_COMMANDS.sub(" ", value)
    value = re.sub(r"\\[dt]frac\b", r"\\frac", value)
    style_wrappers = r"\\(?:mathrm|mathbf|mathit|boldsymbol|bm|text|operatorname\*?)\s*\{([^{}]*)\}"
    value = re.sub(style_wrappers, r"\1", value)
    value = re.sub(r"([_^])\{\s*([A-Za-z0-9])\s*\}", r"\1\2", value)  # x^{2} -> x^2
    value = re.sub(r"\s+", "", value)
    return value


def similarity(first: str, second: str) -> float:
    """Token-level similarity in [0, 1] between two normalized LaTeX strings."""

    tokens_a = tokenize(normalize_for_comparison(first))
    tokens_b = tokenize(normalize_for_comparison(second))
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    return SequenceMatcher(a=tokens_a, b=tokens_b, autojunk=False).ratio()


def _brace_balance(latex: str) -> float:
    """Return 1.0 for balanced grouping and less for every kind of mismatch."""

    penalties = 0
    depth = 0
    for token in tokenize(latex):
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
            if depth < 0:
                penalties += 1
                depth = 0
    penalties += depth
    for left, right in ((r"\left", r"\right"), (r"\begin", r"\end")):
        penalties += abs(latex.count(left) - latex.count(right))
    return max(0.0, 1.0 - 0.25 * penalties)


def _repetition_penalty(latex: str) -> float:
    """Detect the degenerate repetition loops transformer decoders fall into."""

    tokens = tokenize(latex)
    if len(tokens) < 24:
        return 1.0
    worst = 1.0
    for window in (1, 2, 3, 4, 6, 8):
        run_length = 1
        longest = 1
        for index in range(window, len(tokens)):
            if tokens[index] == tokens[index - window]:
                run_length += 1
                longest = max(longest, run_length)
            else:
                run_length = 1
        # `longest` counts token repeats; a phrase repeated more than four
        # times in a row is almost never real mathematics.
        repeats = longest / window
        if repeats >= 5:
            worst = min(worst, max(0.0, 1.0 - (repeats - 4) * 0.2))
    return worst


def structure_score(latex: str) -> float:
    """Score how plausible a LaTeX string is as real recognizer output (0..1)."""

    value = clean_latex(latex)
    if not value:
        return 0.0
    if len(value) > 8000:
        return 0.05
    return _brace_balance(value) * _repetition_penalty(value)


def extract_math(markdown: str) -> list[str]:
    """Extract display and inline TeX math from Pix2Text-flavoured Markdown.

    Kept for compatibility with older clients of this module. Escaped dollar
    signs are not treated as delimiters, and duplicates are retained because a
    repeated equation on a source page can be meaningful.
    """

    token_pattern = re.compile(
        r"(?<!\\)\$\$(?P<display>.+?)(?<!\\)\$\$"
        r"|\\\[(?P<bracket>.+?)\\\]"
        r"|(?<![\\$])\$(?!\$)(?P<inline>.+?)(?<!\\)\$(?!\$)",
        flags=re.DOTALL,
    )
    equations: list[str] = []
    for match in token_pattern.finditer(markdown):
        value = next(group for group in match.groups() if group is not None)
        value = clean_latex(value)
        if value:
            equations.append(value)
    return equations
