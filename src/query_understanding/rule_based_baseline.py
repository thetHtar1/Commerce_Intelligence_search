"""Transparent lexicon-and-pattern baseline for query expression understanding."""

from __future__ import annotations

import csv
import functools
import re
from pathlib import Path
from typing import Any

try:
    from .validate_dataset import DEFAULT_DATA_DIR
except ImportError:  # Support direct execution as a script from the repository root.
    from validate_dataset import DEFAULT_DATA_DIR

DEFAULT_CURRENCY_DATA_DIR = DEFAULT_DATA_DIR.parent / "currency_resolution"


def _currency_pattern_parts() -> tuple[str, str]:
    """Load ISO codes and CLDR symbol spellings for numeric query patterns."""
    alias_path = DEFAULT_CURRENCY_DATA_DIR / "currency_aliases.csv"
    code_path = DEFAULT_CURRENCY_DATA_DIR / "currency_registry.csv"
    fallback = (r"[$€£฿¥₹₽₩₺₫₪₱₴₦₲₡₵₸₭₮₨؋֏₼₾]", r"USD|THB")
    if not alias_path.is_file() or not code_path.is_file():
        return fallback
    with code_path.open("r", encoding="utf-8-sig", newline="") as handle:
        codes = sorted((row["currency_code"] for row in csv.DictReader(handle)), key=len, reverse=True)
    symbols: set[str] = set()
    with alias_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            kinds = set((row.get("alias_types") or "").split("|"))
            alias = (row.get("alias") or "").strip()
            if alias and kinds & {"symbol", "narrow_symbol", "symbol_variant"} and not any(char.isspace() for char in alias):
                symbols.add(alias)
    symbol_pattern = "|".join(re.escape(symbol) for symbol in sorted(symbols, key=len, reverse=True))
    return (symbol_pattern or fallback[0], "|".join(re.escape(code) for code in codes) or fallback[1])


CURRENCY_SYMBOL_PATTERN, CURRENCY_CODE_PATTERN = _currency_pattern_parts()


PRODUCT_CATEGORIES = [
    "washing machine",
    "cleaning spray",
    "water bottle",
    "office chair",
    "running shoes",
    "hiking backpack",
    "hiking shoes",
    "furniture store",
    "cordless vacuum",
    "noise-cancelling headphones",
    "Bluetooth speaker",
    "portable monitor",
    "smartwatch",
    "headphones",
    "dishwasher",
    "refrigerator",
    "conditioner",
    "shampoo",
    "laptop",
    "chair",
    "desk",
    "sofa",
    "speaker",
    "monitor",
    "printer",
    "bottle",
    "sheets",
    "backpack",
    "bag",
    "jacket",
    "watch",
    "sunglasses",
    "tablet",
    "camera",
    "vacuum",
    "detergent",
    "snacks",
    "phone",
    "pan",
]
PRODUCT_CATEGORIES.sort(key=len, reverse=True)

NUMBER = rf"(?:(?:{CURRENCY_SYMBOL_PATTERN})\s*)?\d[\d,]*(?:\.\d+)?"
UNIT = rf"(?:\s*(?:(?:baht|{CURRENCY_CODE_PATTERN})(?!\w)|stars?|GB|TB|kg|grams?|lb|liters?|liter|hours?|days?|inches?|reviews?|x))?"
METRIC_SUFFIX = r"(?:\s+(?:RAM|storage|capacity|battery\s+life|optical\s+zoom|video\s+recording))?"
OPERATOR = (
    r"less\s+than\s+or\s+equal\s+to|greater\s+than\s+or\s+equal\s+to|"
    r"not\s+more\s+than|no\s+more\s+than|no\s+less\s+than|not\s+less\s+than|no\s+higher\s+than|"
    r"no\s+lower\s+than|not\s+exceeding|not\s+above|at\s+most|at\s+least|"
    r"less\s+than|greater\s+than|cheaper\s+than|lighter\s+than|bigger\s+than|"
    r"more\s+than|up\s+to|below|under|over|above|maximum|max|minimum|min|"
    r"between|within|exactly|near|equal\s+to"
)
NUMERIC_CONSTRAINT = re.compile(
    rf"(?:(?P<soft>ideally|preferably)\s+)?"
    rf"(?:(?P<prefix>cost|price|priced|weighs?)\s+)?"
    rf"(?P<operator>{OPERATOR})\s+(?:a\s+)?(?P<first>{NUMBER})"
    rf"(?:\s+(?:and|to)\s+(?P<second>{NUMBER}))?"
    rf"(?P<unit>{UNIT})(?P<suffix>{METRIC_SUFFIX})"
    rf"(?:\s+budget)?",
    flags=re.IGNORECASE,
)
SOFT_BARE_NUMBER = re.compile(
    rf"(?P<soft>ideally|preferably)\s+(?P<first>{NUMBER})"
    rf"(?P<unit>{UNIT})\s+or\s+(?:higher|lower|more|less)",
    flags=re.IGNORECASE,
)
SOFT_PHRASE = re.compile(r"\bpreferably\s+less\b", flags=re.IGNORECASE)
HARD_ATTRIBUTE = re.compile(
    r"\b(?:must\s+(?:be|have)|need\s+(?:a|an|to\s+have)?)\s+[^,;]+?"
    r"(?=\s+and\s+|\s+but\s+|,|;|$)",
    flags=re.IGNORECASE,
)
ONLY_ATTRIBUTE = re.compile(r"\bonly\s+[\w-]+", flags=re.IGNORECASE)
NEGATION = re.compile(
    r"\b(?:without|free\s+from|free\s+of|excluding|except|avoid|do\s+not\s+include|no)\s+"
    r"(?:added\s+|plastic\s+)?[\w-]+(?:\s+parts?)?",
    flags=re.IGNORECASE,
)
NOT_ATTRIBUTE = re.compile(r"\bnot\s+(?!above\b|below\b|less\b|more\b|too\b|heavy\b)[\w-]+", flags=re.IGNORECASE)
COMPARISON = re.compile(
    r"\b(?:cheaper\s+than|less\s+expensive\s+than|more\s+expensive\s+than|"
    r"better\s+rated\s+than|higher\s+rated\s+than|lower\s+priced\s+than|"
    r"similar\s+to|alternative\s+to|instead\s+of|same\s+as|compared\s+with)\s+"
    r"[^,;]+?(?=\s+(?:but|and|under|below|over|above|up\s+to|no\s+more\s+than|at\s+least)\b|,|;|$)",
    flags=re.IGNORECASE,
)

SPECIAL_PATTERNS: tuple[tuple[re.Pattern[str], str, int], ...] = (
    (re.compile(r"\bfor\s+(?:dry\s+hair|sensitive\s+scalp)\b", re.I), "product_attribute", 90),
    (re.compile(r"\bfor\s+(?:travel|small\s+apartment|long\s+hours|beginners|video\s+editing|machine\s+learning|students|everyday\s+use)\b", re.I), "ambiguous_expression", 90),
    (re.compile(r"\bfor\s+\d+\s+lb\s+user\b", re.I), "product_attribute", 90),
    (re.compile(r"\b(?:organic\s+cotton|vegan\s+leather|strong\s+suction|polarized\s+lenses|dedicated\s+GPU|similar\s+features|good\s+battery|high\s+performance|low\s+noise|no\s+assembly\s+required|light-colored)\b", re.I), "product_attribute", 90),
    (re.compile(r"\bat\s+least\s+queen\s+size\b", re.I), "hard_constraint", 100),
    (re.compile(r"\bexactly\s+4K(?:\s+video\s+recording)?\b", re.I), "hard_constraint", 105),
    (re.compile(r"\b(?:not\s+too\s+expensive|reasonably\s+priced|at\s+a\s+reasonable\s+price)\b", re.I), "ambiguous_expression", 95),
    (re.compile(r"\bnot\s+heavy\b", re.I), "soft_preference", 95),
    (re.compile(r"\bsmaller\b", re.I), "comparison", 80),
    (re.compile(r"\bprefer\b", re.I), "soft_preference", 60),
)

ATTRIBUTE_ADJECTIVES = {"lightweight", "compact", "portable", "light", "large", "small"}
SUBJECTIVE_TERMS = {"best", "good", "fast", "strong", "natural", "safe", "healthy", "heavy duty"}


def load_lexicon(path: Path | None = None) -> list[dict[str, str]]:
    path = path or DEFAULT_DATA_DIR / "expression_lexicon.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def load_currency_aliases(path: Path | None = None) -> list[dict[str, str]]:
    path = path or DEFAULT_CURRENCY_DATA_DIR / "currency_aliases.csv"
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _compiled_currency_aliases() -> list[tuple[dict[str, str], re.Pattern[str], bool]]:
    compiled: list[tuple[dict[str, str], re.Pattern[str], bool]] = []
    for row in load_currency_aliases():
        alias = (row.get("alias") or "").strip()
        if not alias:
            continue
        kinds = set((row.get("alias_types") or "").split("|"))
        is_symbol = bool(kinds & {"symbol", "narrow_symbol", "symbol_variant"}) and not any(
            char.isalnum() for char in alias
        )
        pattern = (
            re.compile(re.escape(alias))
            if is_symbol
            else re.compile(rf"(?<!\w){re.escape(alias)}(?=$|\W|\d)", re.IGNORECASE)
        )
        compiled.append((row, pattern, is_symbol))
    return compiled


def resolve_currency(query: str) -> dict[str, Any]:
    """Resolve currency mentions from the CLDR alias table; preserve ambiguous symbols."""
    numeric_matches = list(re.finditer(r"\d[\d,]*(?:\.\d+)?", query))
    if not numeric_matches:
        return {"currency_code": None, "candidate_codes": [], "matches": [], "ambiguous": False}

    hits: list[dict[str, Any]] = []
    for row, pattern, is_symbol in _compiled_currency_aliases():
        alias = (row.get("alias") or "").strip()
        if not alias:
            continue
        candidates = [code for code in (row.get("candidate_codes") or "").split("|") if code]
        for match in pattern.finditer(query):
            distance = min(
                max(number.start() - match.end(), match.start() - number.end(), 0)
                for number in numeric_matches
            )
            if distance > 36:
                continue
            if is_symbol and not re.search(r"\d", query[max(0, match.start() - 4):match.end() + 4]):
                continue
            hits.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "alias": alias,
                    "candidate_codes": candidates,
                    "unique": len(candidates) == 1,
                    "length": match.end() - match.start(),
                    "nearest_number_start": min(
                        numeric_matches,
                        key=lambda number: max(number.start() - match.end(), match.start() - number.end(), 0),
                    ).start(),
                }
            )

    hits.sort(key=lambda hit: (-hit["length"], not hit["unique"], hit["start"]))
    selected: list[dict[str, Any]] = []
    for hit in hits:
        if any(hit["start"] < chosen["end"] and chosen["start"] < hit["end"] for chosen in selected):
            continue
        selected.append(hit)

    unique_hits = [hit for hit in selected if hit["unique"]]
    unique_codes = {hit["candidate_codes"][0] for hit in unique_hits}
    all_candidates = sorted({code for hit in selected for code in hit["candidate_codes"]})
    resolved = next(iter(unique_codes)) if len(unique_codes) == 1 else None
    ambiguous_hits = [hit for hit in selected if not hit["unique"]]
    # A clear code/name mention resolves a generic symbol when both refer to the same amount.
    resolved_same_amount = bool(unique_hits) and all(
        any(hit["nearest_number_start"] == unique["nearest_number_start"] for unique in unique_hits)
        for hit in ambiguous_hits
    )
    ambiguous = bool(selected) and (len(unique_codes) != 1 or (ambiguous_hits and not resolved_same_amount))
    if len(unique_codes) == 1 and (not ambiguous_hits or resolved_same_amount):
        ambiguous = False
        all_candidates = [resolved]
    return {
        "currency_code": resolved if not ambiguous else None,
        "candidate_codes": all_candidates,
        "matches": selected,
        "ambiguous": ambiguous,
    }


def _add(candidates: list[dict[str, Any]], query: str, match: re.Match[str], label: str, priority: int) -> None:
    if match.start() == match.end():
        return
    candidates.append(
        {"start": match.start(), "end": match.end(), "text": query[match.start():match.end()], "label": label, "priority": priority}
    )


def _word_pattern(phrase: str) -> re.Pattern[str] | None:
    if "..." in phrase:
        return None
    return re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", flags=re.IGNORECASE)


def _has_product_context(query: str, start: int, end: int) -> bool:
    context = query[max(0, start - 28):min(len(query), end + 40)]
    return any(re.search(rf"(?<!\w){re.escape(category)}(?!\w)", context, re.I) for category in PRODUCT_CATEGORIES)


def predict_spans(query: str, lexicon: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    """Return non-overlapping (text, label) predictions from hand-written rules."""
    lexicon = lexicon or load_lexicon()
    candidates: list[dict[str, Any]] = []

    for match in NUMERIC_CONSTRAINT.finditer(query):
        label = "soft_preference" if match.group("soft") else "hard_constraint"
        _add(candidates, query, match, label, 110)
    for match in SOFT_BARE_NUMBER.finditer(query):
        _add(candidates, query, match, "soft_preference", 110)
    for match in SOFT_PHRASE.finditer(query):
        _add(candidates, query, match, "soft_preference", 90)

    for match in HARD_ATTRIBUTE.finditer(query):
        _add(candidates, query, match, "hard_constraint", 105)
    for match in ONLY_ATTRIBUTE.finditer(query):
        _add(candidates, query, match, "hard_constraint", 105)
    for pattern, label, priority in SPECIAL_PATTERNS:
        for match in pattern.finditer(query):
            _add(candidates, query, match, label, priority)

    for match in NEGATION.finditer(query):
        phrase = match.group(0).casefold()
        remainder = query[match.start():].casefold()
        if re.match(r"\b(?:not\s+more\s+than|no\s+more\s+than|no\s+less\s+than|not\s+less\s+than|not\s+above|no\s+higher\s+than|no\s+lower\s+than)\b", remainder):
            continue
        if phrase == "no assembly":
            continue
        _add(candidates, query, match, "negation", 100)
    for match in NOT_ATTRIBUTE.finditer(query):
        phrase = match.group(0).casefold()
        _add(candidates, query, match, "negation", 100)

    for match in COMPARISON.finditer(query):
        if re.search(r"\d|[$฿€£]", match.group(0)):
            continue
        _add(candidates, query, match, "comparison", 85)

    for entry in sorted(lexicon, key=lambda item: len(item["expression"]), reverse=True):
        expression = entry.get("expression", "").strip()
        family = entry.get("expression_family", "")
        if family in {"hard_constraint", "negation", "comparison"}:
            continue
        pattern = _word_pattern(expression)
        if pattern is None:
            continue
        for match in pattern.finditer(query):
            label = family
            lowered = expression.casefold()
            if lowered in {"not too expensive", "reasonably priced", "reasonable price"}:
                label = "ambiguous_expression"
            elif family == "ambiguous_expression" and lowered in ATTRIBUTE_ADJECTIVES:
                before = query[max(0, match.start() - 32):match.start()].casefold()
                if re.search(r"\bprefer(?:s|red)?\s+(?:a\s+)?$", before):
                    label = "soft_preference"
                elif _has_product_context(query, match.start(), match.end()):
                    label = "product_attribute"
            elif family == "ambiguous_expression" and lowered == "powerful":
                label = "soft_preference"
            if lowered in SUBJECTIVE_TERMS and family == "product_attribute":
                label = "ambiguous_expression"
            _add(candidates, query, match, label, 50)

    candidates.sort(key=lambda item: (-item["priority"], -(item["end"] - item["start"]), item["start"], item["label"]))
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if any(candidate["start"] < item["end"] and item["start"] < candidate["end"] for item in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda item: item["start"])


def _field_for(text: str, label: str, currency_present: bool = False) -> str:
    value = text.casefold()
    if any(token in value for token in ("$", "baht", "price", "budget", "expensive", "cheap", "affordable")):
        return "price"
    if "star" in value or "rated" in value or "rating" in value:
        return "rating"
    if "review" in value:
        return "review_count"
    if "kg" in value or "gram" in value or "heavy" in value or "lightweight" in value or value == "light":
        return "weight"
    if "gb" in value or "storage" in value or "ram" in value:
        return "storage"
    if "day" in value:
        return "delivery_time"
    if "bluetooth" in value or "wireless" in value:
        return "connectivity"
    if "hair" in value:
        return "hair_type"
    if "scalp" in value:
        return "scalp_type"
    if "fragrance" in value or "scent" in value:
        return "fragrance"
    if "leather" in value:
        return "material"
    if "color" in value or "black" in value:
        return "color"
    if "size" in value or "compact" in value or "smaller" in value:
        return "size"
    if "similar" in value or "alternative" in value or "brand" in value:
        return "product_identity"
    if currency_present and re.search(r"\d", text):
        return "price"
    return "product_property" if label == "product_attribute" else "query_preference"


def _numeric_slots(text: str, currency_code: str | None = None) -> tuple[str, Any, str | None] | None:
    lowered = text.casefold()
    op_match = re.search(OPERATOR, lowered, flags=re.IGNORECASE)
    number_matches = list(re.finditer(r"\d[\d,]*(?:\.\d+)?", text))
    if not number_matches:
        return None
    values = [float(match.group(0).replace(",", "")) for match in number_matches]
    if all(value.is_integer() for value in values):
        values = [int(value) for value in values]
    if not op_match:
        return None
    operator_text = re.sub(r"\s+", " ", op_match.group(0).casefold())
    if "between" in operator_text:
        operator = "between"
        value: Any = {"min": values[0], "max": values[1]} if len(values) > 1 else values[0]
    elif operator_text in {"less than", "cheaper than", "lighter than", "bigger than", "more than"}:
        operator = "lt" if operator_text in {"less than", "cheaper than", "lighter than"} else "gt"
        value = values[0]
    elif operator_text in {"under", "below", "no more than", "at most", "maximum", "max", "not exceeding", "no higher than", "not above", "up to", "within"}:
        operator = "lte"
        value = values[0]
    elif operator_text in {"over", "above", "at least", "no less than", "not less than", "no lower than", "minimum", "min", "greater than", "greater than or equal to"}:
        operator = "gte" if operator_text in {"at least", "no less than", "not less than", "no lower than", "minimum", "min", "greater than or equal to"} else "gt"
        value = values[0]
    elif operator_text in {"exactly", "equal to"}:
        operator, value = "eq", values[0]
    elif operator_text == "near":
        operator, value = "near", values[0]
    else:
        operator, value = "eq", values[0]

    currency_in_text = resolve_currency(text)
    if currency_in_text["currency_code"]:
        unit = currency_in_text["currency_code"]
    elif currency_code:
        unit = currency_code
    elif "star" in lowered:
        unit = "stars"
    elif "kg" in lowered:
        unit = "kg"
    elif "gram" in lowered:
        unit = "grams"
    elif "lb" in lowered:
        unit = "lb"
    elif "gb" in lowered:
        unit = "GB"
    elif "tb" in lowered:
        unit = "TB"
    elif "day" in lowered:
        unit = "days"
    elif "hour" in lowered:
        unit = "hours"
    elif "inch" in lowered:
        unit = "inches"
    elif "review" in lowered:
        unit = "reviews"
    else:
        unit = None
    return operator, value, unit


def predict_intent(query: str, lexicon: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Project baseline spans into the agreed V1 query-intent object."""
    lexicon = lexicon or load_lexicon()
    normalized = " ".join(query.casefold().split())
    category = next(
        (
            item.casefold()
            for item in PRODUCT_CATEGORIES
            if re.search(rf"(?<!\w){re.escape(item)}(?!\w)", query, flags=re.IGNORECASE)
        ),
        None,
    )
    intent: dict[str, Any] = {
        "original_query": query,
        "normalized_query": normalized,
        "language": "en" if query.isascii() else "und",
        "query_type": "natural_language",
        "product_category": category,
        "attributes": [],
        "constraints": [],
        "soft_preferences": [],
        "ambiguities": [],
        "needs_clarification": False,
    }
    currency_resolution = resolve_currency(query)
    if currency_resolution["ambiguous"]:
        ambiguous_hits = [hit for hit in currency_resolution["matches"] if not hit["unique"]]
        source_text = ambiguous_hits[0]["alias"] if ambiguous_hits else ", ".join(
            hit["alias"] for hit in currency_resolution["matches"]
        )
        intent["ambiguities"].append(
            {
                "text": source_text,
                "attribute": "currency",
                "reason": "currency_alias_ambiguous",
                "candidate_codes": currency_resolution["candidate_codes"],
            }
        )
        intent["needs_clarification"] = True
    for span in predict_spans(query, lexicon):
        text, label = span["text"], span["label"]
        span_numbers = {
            match.start() + span["start"]
            for match in re.finditer(r"\d[\d,]*(?:\.\d+)?", text)
        }
        currency_present = any(
            hit["nearest_number_start"] in span_numbers
            for hit in currency_resolution["matches"]
        )
        currency_code = currency_resolution["currency_code"] if currency_present else None
        field = _field_for(text, label, currency_present)
        numeric = _numeric_slots(text, currency_code=currency_code if field == "price" else None)
        if label == "product_attribute":
            value = text.casefold().removeprefix("for ").replace("-", " ")
            if field == "hair_type" and "dry" in value:
                value = "dry"
            intent["attributes"].append({"name": field, "value": value})
        elif label == "hard_constraint":
            if numeric:
                operator, value, unit = numeric
            else:
                operator = "required"
                value = text.casefold()
                value = re.sub(r"^(?:must be|must have|need(?: a| an)?|only)\s+", "", value)
                unit = None
            intent["constraints"].append(
                {"field": field, "operator": operator, "value": value, "unit": unit, "priority": "hard", "source_text": text}
            )
        elif label == "soft_preference":
            preference: dict[str, Any] = {
                "field": field,
                "preference": re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_"),
                "source_text": text,
            }
            if numeric:
                preference["operator"], preference["value"], preference["unit"] = numeric
            intent["soft_preferences"].append(preference)
        elif label == "negation":
            value = re.sub(r"^(?:without|excluding|except|avoid|not|free from|free of)\s+", "", text, flags=re.I)
            intent["constraints"].append(
                {"field": field, "operator": "exclude", "value": value, "unit": None, "priority": "hard", "source_text": text}
            )
        elif label == "comparison":
            relation = text.casefold().split()[0]
            intent["soft_preferences"].append(
                {"field": field, "relation": relation, "reference": text, "source_text": text}
            )
        elif label == "ambiguous_expression":
            intent["ambiguities"].append(
                {"text": text, "attribute": field, "reason": "criterion_unclear"}
            )
            if "near me" in text.casefold():
                intent["needs_clarification"] = True
    return intent
