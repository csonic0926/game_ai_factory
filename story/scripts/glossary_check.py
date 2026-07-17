#!/usr/bin/env python3
"""Validate and apply the canonical adapter GLOSSARY.csv review aid.

GLOSSARY.csv is this checker's only proprietary-term source. The checker has
no WORLD_RULES, style-guide, locale-prose, or other termbase fallback; callers
skip glossary-only checks when the adapter capability is NOT_AVAILABLE.

Examples:
  python3 glossary_check.py --glossary <ADAPTER>/GLOSSARY.csv ARTIFACT.md
  python3 glossary_check.py --glossary ... --baseline BEFORE.md AFTER.md
  python3 glossary_check.py --glossary ... \
      --locale en=client/locales/en.json \
      --locale zh-TW=client/locales/zh-TW.json \
      --locale ko=client/locales/ko.json
  python3 glossary_check.py --glossary ... --extract-cleanroom zh-TW DRAFT.md

The checker deliberately does not guess synonyms or infer new world terms.
Those remain review-gate/User judgments. It does validate the CSV, report
exact banned/deprecated/pending occurrences, preserve protected terms across a
before/after rewrite, and compare registered forms at aligned locale keys.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FIELDS = [
    "term_id",
    "zh_TW",
    "en",
    "ko",
    "referent",
    "register",
    "variant_of",
    "speaker_scope",
    "dialogue_protected",
    "status",
    "provenance",
    "notes",
]
LOCALE_COLUMNS = {"zh-TW": "zh_TW", "zh_TW": "zh_TW", "en": "en", "ko": "ko"}
REGISTERS = {"formal", "folk", "both"}
STATUSES = {"canon", "pending", "banned", "deprecated"}
TERM_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
SCOPE_RE = TERM_ID_RE

# Curly/square dialogue marks plus ordinary double-quoted prose. JSON locale
# mode bypasses this extractor and checks decoded string values directly.
QUOTED_RE = re.compile(r"「([^「」]*)」|『([^『』]*)』|\u201c([^\u201c\u201d]*)\u201d|\"([^\"\n]+)\"")


@dataclass(frozen=True)
class Term:
    term_id: str
    zh_TW: str
    en: str
    ko: str
    referent: str
    register: str
    variant_of: str
    speaker_scope: str
    dialogue_protected: bool
    status: str
    provenance: str
    notes: str

    def form(self, locale: str) -> str:
        return getattr(self, LOCALE_COLUMNS[locale])


class GlossaryError(ValueError):
    pass


def load_glossary(path: Path) -> tuple[list[Term], list[str]]:
    warnings: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise GlossaryError(
                f"header mismatch: expected {','.join(FIELDS)}; "
                f"got {','.join(reader.fieldnames or [])}"
            )
        raw_rows = list(reader)

    terms: list[Term] = []
    seen: set[str] = set()
    for line_no, row in enumerate(raw_rows, 2):
        term_id = row["term_id"].strip()
        prefix = f"CSV row {line_no} ({term_id or 'missing term_id'})"
        if not TERM_ID_RE.fullmatch(term_id):
            raise GlossaryError(f"{prefix}: term_id must be snake_case")
        if term_id in seen:
            raise GlossaryError(f"{prefix}: duplicate term_id")
        seen.add(term_id)

        register = row["register"].strip()
        if register not in REGISTERS:
            raise GlossaryError(f"{prefix}: invalid register {register!r}")
        status = row["status"].strip()
        if status not in STATUSES:
            raise GlossaryError(f"{prefix}: invalid status {status!r}")
        protected_raw = row["dialogue_protected"].strip().lower()
        if protected_raw not in {"true", "false"}:
            raise GlossaryError(f"{prefix}: dialogue_protected must be true or false")
        protected = protected_raw == "true"
        scope = row["speaker_scope"].strip()
        if scope not in {"all", "villagers", "design_only"} and not SCOPE_RE.fullmatch(scope):
            raise GlossaryError(f"{prefix}: invalid speaker_scope {scope!r}")
        if not row["referent"].strip():
            raise GlossaryError(f"{prefix}: referent is required")
        if not row["provenance"].strip():
            raise GlossaryError(f"{prefix}: provenance is required")
        if not any(row[name].strip() for name in ("zh_TW", "en", "ko")):
            raise GlossaryError(f"{prefix}: at least one locale form is required")
        if status == "banned" and protected:
            raise GlossaryError(f"{prefix}: banned rows must not be dialogue_protected")
        if status == "canon":
            missing = [name for name in ("zh_TW", "en", "ko") if not row[name].strip()]
            if missing:
                warnings.append(
                    f"{prefix}: canon row has no registered {', '.join(missing)} form; "
                    "workers must nominate rather than infer it"
                )

        terms.append(
            Term(
                term_id=term_id,
                zh_TW=row["zh_TW"].strip(),
                en=row["en"].strip(),
                ko=row["ko"].strip(),
                referent=row["referent"].strip(),
                register=register,
                variant_of=row["variant_of"].strip(),
                speaker_scope=scope,
                dialogue_protected=protected,
                status=status,
                provenance=row["provenance"].strip(),
                notes=row["notes"].strip(),
            )
        )

    by_id = {term.term_id: term for term in terms}
    for term in terms:
        if term.variant_of:
            if term.variant_of == term.term_id:
                raise GlossaryError(f"{term.term_id}: variant_of cannot point to itself")
            if term.variant_of not in by_id:
                raise GlossaryError(f"{term.term_id}: unknown variant_of {term.variant_of!r}")
    return terms, warnings


def quoted_text(text: str) -> str:
    matches = [next(group for group in match.groups() if group is not None) for match in QUOTED_RE.finditer(text)]
    return "\n".join(matches)


def form_hits(text: str, terms: Iterable[Term], statuses: set[str]) -> list[tuple[Term, str, int]]:
    hits: list[tuple[Term, str, int]] = []
    for term in terms:
        if term.status not in statuses:
            continue
        for form in {term.zh_TW, term.en, term.ko} - {""}:
            count = text.count(form)
            if count:
                hits.append((term, form, count))
    return hits


def protected_counts(text: str, terms: Iterable[Term]) -> Counter[tuple[str, str]]:
    dialogue = quoted_text(text)
    counts: Counter[tuple[str, str]] = Counter()
    for term in terms:
        if term.status != "canon" or not term.dialogue_protected:
            continue
        for form in {term.zh_TW, term.en, term.ko} - {""}:
            counts[(term.term_id, form)] = dialogue.count(form)
    return counts


def scan_artifact(path: Path, terms: list[Term], baseline: Path | None) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    dialogue = quoted_text(text)
    errors = 0
    warnings = 0
    print(f"ARTIFACT {path}")

    banned = form_hits(text, terms, {"banned"})
    for term, form, count in banned:
        print(f"  ERROR banned {term.term_id} [{form}] x{count}")
        errors += 1
    deprecated = form_hits(dialogue, terms, {"deprecated"})
    for term, form, count in deprecated:
        print(f"  WARN deprecated dialogue form {term.term_id} [{form}] x{count}")
        warnings += 1
    pending = form_hits(dialogue, terms, {"pending"})
    for term, form, count in pending:
        print(f"  WARN pending dialogue form {term.term_id} [{form}] x{count}; USER ruling still open")
        warnings += 1

    active = form_hits(dialogue, terms, {"canon"})
    protected_ids = {term.term_id for term, _, _ in active if term.dialogue_protected}
    print(
        f"  exact scan: banned={len(banned)} deprecated={len(deprecated)} "
        f"pending={len(pending)} protected_term_ids={len(protected_ids)}"
    )

    if baseline:
        before = protected_counts(baseline.read_text(encoding="utf-8"), terms)
        after = protected_counts(text, terms)
        for key, before_count in sorted(before.items()):
            if before_count and after[key] < before_count:
                term_id, form = key
                print(
                    f"  ERROR protected form reduced: {term_id} [{form}] "
                    f"before={before_count} after={after[key]}"
                )
                errors += 1
        print(f"  protected diff baseline={baseline}")

    print("  NOTE synonym replacement and unregistered-term discovery require gate/USER review")
    return errors, warnings


def flatten_json_strings(value: object, prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_json_strings(child, child_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(flatten_json_strings(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        result[prefix] = value
    return result


def parse_locale_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("locale must use LOCALE=PATH")
    locale, raw_path = raw.split("=", 1)
    if locale not in LOCALE_COLUMNS:
        raise argparse.ArgumentTypeError(f"unsupported locale {locale!r}; use en, zh-TW, or ko")
    return locale, Path(raw_path)


def extract_cleanroom(
    locale: str, artifacts: list[Path], terms: list[Term], speakers: list[str]
) -> tuple[int, int]:
    source_dialogue = ""
    if artifacts:
        source_dialogue = "\n".join(
            quoted_text(path.read_text(encoding="utf-8")) for path in artifacts
        )
    speaker_set = set(speakers)

    protected: list[tuple[str, str, str, str]] = []
    banned: list[tuple[str, str]] = []
    warnings = 0
    for term in terms:
        form = term.form(locale)
        if term.status == "banned" and form:
            banned.append((term.term_id, form))
            continue
        if term.status != "canon" or not term.dialogue_protected:
            continue
        if term.speaker_scope == "design_only":
            continue
        if speaker_set and term.speaker_scope != "all" and term.speaker_scope not in speaker_set:
            continue
        if not form:
            print(f"WARN no registered {locale} form for protected {term.term_id}")
            warnings += 1
            continue
        if source_dialogue and form not in source_dialogue:
            continue
        protected.append((term.term_id, form, term.register, term.speaker_scope))

    print(f"CLEAN-ROOM CONSTRAINTS locale={locale}")
    if artifacts:
        print("source=" + ", ".join(str(path) for path in artifacts))
    print("PROTECTED — keep these exact when they occur in the source:")
    if protected:
        for term_id, form, register, scope in protected:
            print(f"- {form} ({term_id}; register={register}; speaker_scope={scope})")
    else:
        print("- NONE")
    print("BANNED — do not use:")
    if banned:
        for term_id, form in banned:
            print(f"- {form} ({term_id})")
    else:
        print("- NONE")
    return 0, warnings


def scan_locales(locale_args: list[tuple[str, Path]], terms: list[Term]) -> tuple[int, int]:
    catalogs: dict[str, dict[str, str]] = {}
    errors = 0
    warnings = 0
    for locale, path in locale_args:
        if locale in catalogs:
            raise GlossaryError(f"duplicate locale argument: {locale}")
        catalogs[locale] = flatten_json_strings(json.loads(path.read_text(encoding="utf-8")))
    print("LOCALE MODE " + ", ".join(f"{locale}={path}" for locale, path in locale_args))
    source_locale = "zh-TW" if "zh-TW" in catalogs else ("zh_TW" if "zh_TW" in catalogs else next(iter(catalogs)))
    print(f"  source locale for aligned-term triggers={source_locale}")

    all_keys = sorted(set().union(*(catalog.keys() for catalog in catalogs.values())))
    for term in terms:
        if term.status != "canon" or not term.dialogue_protected or term.speaker_scope == "design_only":
            continue
        source_form = term.form(source_locale)
        registered = {locale: term.form(locale) for locale in catalogs if term.form(locale)}
        if len(registered) < 2:
            continue
        for key in all_keys:
            values = {locale: catalogs[locale].get(key, "") for locale in catalogs}
            if not source_form or source_form not in values[source_locale]:
                continue
            present = [locale for locale, form in registered.items() if form in values[locale]]
            missing = [locale for locale, form in registered.items() if form not in values[locale]]
            if missing:
                print(
                    f"  ERROR locale mismatch key={key} term={term.term_id}: "
                    f"present={','.join(present)} missing={','.join(missing)}"
                )
                errors += 1

    for locale, catalog in catalogs.items():
        text = "\n".join(catalog.values())
        for term, form, count in form_hits(text, terms, {"banned"}):
            print(f"  ERROR banned locale form {locale} {term.term_id} [{form}] x{count}")
            errors += 1
    print(f"  aligned keys checked={len(all_keys)}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--baseline", type=Path, help="pre-rewrite artifact for protected-term diff")
    parser.add_argument(
        "--extract-cleanroom",
        choices=sorted(LOCALE_COLUMNS),
        metavar="LOCALE",
        help="print a plain-language protected/banned list; artifacts limit protected forms to source dialogue",
    )
    parser.add_argument(
        "--speaker",
        action="append",
        default=[],
        help="speaker scope/id for clean-room extraction; repeat for a multi-speaker scene",
    )
    parser.add_argument(
        "--locale",
        action="append",
        default=[],
        type=parse_locale_arg,
        metavar="LOCALE=PATH",
        help="aligned JSON locale catalog; repeat for en/zh-TW/ko",
    )
    parser.add_argument("artifacts", nargs="*", type=Path)
    args = parser.parse_args()
    if not args.artifacts and not args.locale and not args.extract_cleanroom:
        parser.error("provide at least one artifact, --locale catalog, or --extract-cleanroom")
    if args.baseline and len(args.artifacts) != 1:
        parser.error("--baseline requires exactly one revised artifact")
    if args.baseline and args.extract_cleanroom:
        parser.error("--baseline cannot be combined with --extract-cleanroom")
    if args.speaker and not args.extract_cleanroom:
        parser.error("--speaker requires --extract-cleanroom")

    try:
        terms, schema_warnings = load_glossary(args.glossary)
        print(f"GLOSSARY {args.glossary}: {len(terms)} rows, schema valid")
        for warning in schema_warnings:
            print(f"  WARN {warning}")
        errors = 0
        warnings = len(schema_warnings)
        if args.extract_cleanroom:
            extract_errors, extract_warnings = extract_cleanroom(
                args.extract_cleanroom, args.artifacts, terms, args.speaker
            )
            errors += extract_errors
            warnings += extract_warnings
        else:
            for artifact in args.artifacts:
                artifact_errors, artifact_warnings = scan_artifact(artifact, terms, args.baseline)
                errors += artifact_errors
                warnings += artifact_warnings
        if args.locale:
            locale_errors, locale_warnings = scan_locales(args.locale, terms)
            errors += locale_errors
            warnings += locale_warnings
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, GlossaryError) as exc:
        print(f"GLOSSARY ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {'FAIL' if errors else 'PASS'} errors={errors} warnings={warnings}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
