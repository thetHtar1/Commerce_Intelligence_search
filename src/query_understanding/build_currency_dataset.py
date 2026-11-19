"""Build a versioned currency registry and synthetic query dataset from CLDR JSON."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "currency"
OUTPUT_DIR = REPO_ROOT / "data" / "training" / "currency_resolution"
LOCALES = ("en", "my", "th")
SOURCES = {
    "currency_data": "cldr_49_currency_data.json",
    "en": "cldr_49_en_currencies.json",
    "my": "cldr_49_my_currencies.json",
    "th": "cldr_49_th_currencies.json",
}

ALIAS_FIELD_TYPES = {
    "displayName": "display_name",
    "displayName-count-one": "singular_name",
    "displayName-count-other": "plural_name",
    "symbol": "symbol",
    "symbol-alt-narrow": "narrow_symbol",
    "symbol-alt-variant": "symbol_variant",
}

AMOUNTS = ("200", "500", "1200")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_alias(value: str) -> str:
    return " ".join(value.casefold().split())


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _locale_currencies(locale: str) -> dict[str, dict[str, str]]:
    data = _load_json(RAW_DIR / SOURCES[locale])
    main = data["main"]
    locale_root = main[next(iter(main))]
    return locale_root["numbers"]["currencies"]


def _active_currency_metadata(currency_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    regions = currency_data["region"]
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"regions": [], "from_dates": []})
    for region, entries in regions.items():
        for entry in entries:
            for code, metadata in entry.items():
                if metadata.get("_to") or metadata.get("_tender", "true").casefold() == "false":
                    continue
                result[code]["regions"].append(region)
                if metadata.get("_from"):
                    result[code]["from_dates"].append(metadata["_from"])
    return result


def _build_registry(
    currency_data: dict[str, Any],
    localized: dict[str, dict[str, dict[str, str]]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]], str]:
    supplemental = currency_data["supplemental"]
    version = supplemental["version"].get("_cldrVersion", "unknown")
    currency_metadata = supplemental["currencyData"]
    active = _active_currency_metadata(currency_metadata)
    fractions = currency_metadata["fractions"]
    default_fraction = fractions.get("DEFAULT", {})
    codes = sorted(localized["en"])
    registry_rows: list[dict[str, Any]] = []
    aliases_by_normalized: dict[str, list[dict[str, str]]] = defaultdict(list)

    for code in codes:
        english = localized["en"].get(code, {})
        metadata = active.get(code, {"regions": [], "from_dates": []})
        fraction = fractions.get(code, default_fraction)
        registry_rows.append(
            {
                "currency_code": code,
                "en_display_name": english.get("displayName", ""),
                "en_singular_name": english.get("displayName-count-one", ""),
                "en_plural_name": english.get("displayName-count-other", ""),
                "en_symbol": english.get("symbol", ""),
                "en_narrow_symbol": english.get("symbol-alt-narrow", ""),
                "my_display_name": localized["my"].get(code, {}).get("displayName", ""),
                "th_display_name": localized["th"].get(code, {}).get("displayName", ""),
                "currency_status": "current_tender" if metadata["regions"] else "historical_or_non_tender",
                "active_tender_regions": "|".join(sorted(set(metadata["regions"]))),
                "first_tender_from": min(metadata["from_dates"], default=""),
                "minor_unit_digits": fraction.get("_digits", default_fraction.get("_digits", "2")),
                "cash_digits": fraction.get("_cashDigits", fraction.get("_digits", default_fraction.get("_digits", "2"))),
                "cldr_version": version,
            }
        )

        # ISO code is always an unambiguous alias; names and symbols are sourced from CLDR.
        aliases_by_normalized[_normalize_alias(code)].append(
            {"alias": code, "locale": "und", "alias_type": "iso_code", "currency_code": code}
        )
        for locale in LOCALES:
            for field, alias_type in ALIAS_FIELD_TYPES.items():
                value = localized[locale].get(code, {}).get(field, "").strip()
                if not value or "¤" in value:
                    continue
                aliases_by_normalized[_normalize_alias(value)].append(
                    {"alias": value, "locale": locale, "alias_type": alias_type, "currency_code": code}
                )

        # Bare currency-unit forms occur in shopping queries ("200 baht", "50 dollars").
        # Preserve collisions such as "dollars" as ambiguous candidate lists.
        if metadata["regions"]:
            for field in ("displayName-count-one", "displayName-count-other"):
                name = english.get(field, "").strip()
                words = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", name.casefold(), flags=re.UNICODE)
                if words:
                    core_alias = words[-1]
                    if not any(char.isdigit() for char in core_alias):
                        aliases_by_normalized[_normalize_alias(core_alias)].append(
                            {
                                "alias": core_alias,
                                "locale": "en",
                                "alias_type": "currency_name_core",
                                "currency_code": code,
                            }
                        )

    alias_rows: list[dict[str, Any]] = []
    for normalized, records in sorted(aliases_by_normalized.items()):
        candidate_codes = sorted({record["currency_code"] for record in records})
        # Prefer ISO code as the preserved spelling only for its exact normalized key.
        preferred = sorted(
            records,
            key=lambda record: (
                record["alias_type"] != "iso_code",
                record["locale"] != "en",
                len(record["alias"]),
                record["alias"].casefold(),
            ),
        )[0]
        alias = preferred["alias"]
        alias_id = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        alias_types = sorted({record["alias_type"] for record in records})
        locales = sorted({record["locale"] for record in records})
        unique = len(candidate_codes) == 1
        letters_or_code = any(char.isalpha() for char in alias) or "iso_code" in alias_types
        symbol_has_amount = any(kind in alias_types for kind in ("symbol", "narrow_symbol", "symbol_variant"))
        alias_rows.append(
            {
                "alias_id": alias_id,
                "alias": alias,
                "normalized_alias": normalized,
                "locales": "|".join(locales),
                "alias_types": "|".join(alias_types),
                "candidate_codes": "|".join(candidate_codes),
                "candidate_count": len(candidate_codes),
                "resolution_status": "unique" if unique else "ambiguous",
                "training_eligible": str(unique and (letters_or_code or symbol_has_amount)).lower(),
            }
        )
    return registry_rows, alias_rows, version


def _alias_query_templates(locale: str, alias: str, alias_types: set[str]) -> list[tuple[str, str]]:
    is_code = "iso_code" in alias_types
    is_symbol = bool(alias_types & {"symbol", "narrow_symbol", "symbol_variant"}) and not any(
        char.isalpha() for char in alias
    )
    templates: list[tuple[str, str]] = []
    if locale == "en":
        if is_symbol:
            patterns = [
                ("en_symbol_01", "Find shampoo under {alias}{amount}."),
                ("en_symbol_02", "Show shampoo priced up to {alias}{amount}."),
                ("en_symbol_03", "Search for shampoo within a budget of {alias}{amount}."),
                ("en_symbol_04", "I need shampoo costing at most {alias}{amount}."),
            ]
        else:
            patterns = [
                ("en_named_01", "Find shampoo under {amount} {alias}."),
                ("en_named_02", "Show shampoo priced up to {amount} {alias}."),
                ("en_named_03", "Search for shampoo within a budget of {amount} {alias}."),
                ("en_named_04", "I need shampoo costing at most {amount} {alias}."),
            ]
    elif locale == "my":
        patterns = [
            ("my_01", "ခေါင်းလျှော်ရည်ကို {amount} {alias} အောက်နဲ့ ရှာပါ။"),
            ("my_02", "ခေါင်းလျှော်ရည်အတွက် {amount} {alias} ဘတ်ဂျက်ထားပါ။"),
            ("my_03", "{amount} {alias} ထက်မကျော်တဲ့ ခေါင်းလျှော်ရည် ပြပါ။"),
            ("my_04", "{amount} {alias} အောက် ဈေးရှိတဲ့ ခေါင်းလျှော်ရည် လိုချင်ပါတယ်။"),
        ]
    else:
        if is_symbol:
            patterns = [
                ("th_symbol_01", "ค้นหาแชมพูราคาไม่เกิน {alias}{amount}"),
                ("th_symbol_02", "ขอแชมพูงบประมาณ {alias}{amount}"),
                ("th_symbol_03", "แสดงแชมพูที่ราคาต่ำกว่า {alias}{amount}"),
                ("th_symbol_04", "ต้องการแชมพูราคาไม่เกิน {alias}{amount}"),
            ]
        else:
            patterns = [
                ("th_named_01", "ค้นหาแชมพูราคาไม่เกิน {amount} {alias}"),
                ("th_named_02", "ขอแชมพูงบประมาณ {amount} {alias}"),
                ("th_named_03", "แสดงแชมพูที่ราคาต่ำกว่า {amount} {alias}"),
                ("th_named_04", "ต้องการแชมพูราคาไม่เกิน {amount} {alias}"),
            ]
    # Codes can be used in any of the supported query languages.
    if is_code and locale != "en":
        patterns = [
            (f"{locale}_code_01", ("ခေါင်းလျှော်ရည်ကို {amount} {alias} အောက်နဲ့ ရှာပါ။" if locale == "my" else "ค้นหาแชมพูราคาไม่เกิน {amount} {alias}")),
            (f"{locale}_code_02", ("ခေါင်းလျှော်ရည်အတွက် {amount} {alias} ဘတ်ဂျက်ထားပါ။" if locale == "my" else "ขอแชมพูงบประมาณ {amount} {alias}")),
            (f"{locale}_code_03", ("{amount} {alias} ထက်မကျော်တဲ့ ခေါင်းလျှော်ရည် ပြပါ။" if locale == "my" else "แสดงแชมพูที่ราคาต่ำกว่า {amount} {alias}")),
            (f"{locale}_code_04", ("{amount} {alias} အောက် ဈေးရှိတဲ့ ခေါင်းလျှော်ရည် လိုချင်ပါတယ်။" if locale == "my" else "ต้องการแชมพูราคาไม่เกิน {amount} {alias}")),
        ]
    return [(template_id, pattern.format(alias=alias, amount="{amount}")) for template_id, pattern in patterns]


def _build_examples(alias_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for alias_row in alias_rows:
        candidate_codes = alias_row["candidate_codes"].split("|")
        code = candidate_codes[0] if len(candidate_codes) == 1 else ""
        locales = set(alias_row["locales"].split("|")) - {"und"}
        alias_types = set(alias_row["alias_types"].split("|"))
        alias = alias_row["alias"]
        if "iso_code" in alias_types:
            locales.update(("en", "my", "th"))
        for locale in sorted(locales):
            if locale not in LOCALES:
                continue
            for template_id, query_template in _alias_query_templates(locale, alias, alias_types):
                for amount in AMOUNTS:
                    query = query_template.format(amount=amount)
                    key = (_normalize_alias(query), template_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    example_id = hashlib.sha1(f"{template_id}\0{query}\0{code}".encode("utf-8")).hexdigest()[:16]
                    examples.append(
                        {
                            "example_id": example_id,
                            "query": query,
                            "currency_code": code,
                            "currency_alias": alias,
                            "alias_id": alias_row["alias_id"],
                            "alias_types": "|".join(sorted(alias_types)),
                            "locale": locale,
                            "query_template_id": template_id,
                            "data_origin": "synthetic_cldr_alias_template",
                            "resolution_status": alias_row["resolution_status"],
                            "candidate_codes": alias_row["candidate_codes"],
                            "training_eligible": alias_row["training_eligible"],
                        }
                    )
    return sorted(examples, key=lambda row: (row["query_template_id"], row["example_id"]))


def build(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    missing = [str(RAW_DIR / filename) for filename in SOURCES.values() if not (RAW_DIR / filename).is_file()]
    if missing:
        raise FileNotFoundError("Missing CLDR source file(s):\n" + "\n".join(missing))
    currency_data = _load_json(RAW_DIR / SOURCES["currency_data"])
    localized = {locale: _locale_currencies(locale) for locale in LOCALES}
    registry, aliases, version = _build_registry(currency_data, localized)
    examples = _build_examples(aliases)

    _write_csv(
        output_dir / "currency_registry.csv",
        registry,
        [
            "currency_code", "en_display_name", "en_singular_name", "en_plural_name", "en_symbol",
            "en_narrow_symbol", "my_display_name", "th_display_name", "currency_status",
            "active_tender_regions", "first_tender_from", "minor_unit_digits", "cash_digits", "cldr_version",
        ],
    )
    _write_csv(
        output_dir / "currency_aliases.csv",
        aliases,
        [
            "alias_id", "alias", "normalized_alias", "locales", "alias_types", "candidate_codes",
            "candidate_count", "resolution_status", "training_eligible",
        ],
    )
    example_columns = [
        "example_id", "query", "currency_code", "currency_alias", "alias_id", "alias_types", "locale",
        "query_template_id", "data_origin", "resolution_status", "candidate_codes", "training_eligible",
    ]
    _write_csv(output_dir / "currency_query_examples.csv", examples, example_columns)
    jsonl_path = output_dir / "currency_query_examples.jsonl"
    jsonl_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in examples),
        encoding="utf-8",
    )

    source_manifest = {}
    for source_name, filename in SOURCES.items():
        content = (RAW_DIR / filename).read_bytes()
        source_manifest[source_name] = {
            "file": f"data/raw/currency/{filename}",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    manifest = {
        "dataset": "currency_resolution_v1",
        "cldr_version": version,
        "currencies": len(registry),
        "current_tender_currencies": sum(row["currency_status"] == "current_tender" for row in registry),
        "historical_or_non_tender_currencies": sum(row["currency_status"] != "current_tender" for row in registry),
        "aliases": len(aliases),
        "unambiguous_aliases": sum(row["resolution_status"] == "unique" for row in aliases),
        "ambiguous_aliases": sum(row["resolution_status"] == "ambiguous" for row in aliases),
        "query_examples": len(examples),
        "trainable_query_examples": sum(row["training_eligible"] == "true" for row in examples),
        "locales": list(LOCALES),
        "sources": source_manifest,
    }
    (output_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    manifest = build(args.output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
