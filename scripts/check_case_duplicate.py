#!/usr/bin/env python3
"""Screen a school and case enterprise against the bundled official title index."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DUPLICATES = ROOT / "references" / "duplicate-list-2025.csv"
AWARDS = ROOT / "references" / "award-titles-2025.csv"


def normalize(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)
    return value


def aliases(value: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[|,，;；]", value) if p.strip()]
    return parts or [value.strip()]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def enterprise_match(alias: str, title: str) -> tuple[str, float]:
    needle = normalize(alias)
    haystack = normalize(title)
    if not needle or not haystack:
        return "none", 0.0
    if needle in haystack:
        return "exact-substring", 1.0
    match = SequenceMatcher(None, needle, haystack).find_longest_match()
    coverage = match.size / len(needle)
    if len(needle) >= 3 and coverage >= 0.8:
        return "fuzzy-coverage", coverage
    return "none", coverage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a school and enterprise against the bundled 2025 official title index."
    )
    parser.add_argument("--school", required=True, help="Official full school name")
    parser.add_argument(
        "--enterprise",
        required=True,
        help="Enterprise name; separate brand aliases with |",
    )
    parser.add_argument("--title", default="", help="Optional proposed work title")
    parser.add_argument("--top", type=int, default=10, help="Maximum matches to show")
    args = parser.parse_args()

    duplicate_rows = read_rows(DUPLICATES)
    award_rows = read_rows(AWARDS)
    school_norm = normalize(args.school)
    enterprise_aliases = aliases(args.enterprise)

    same_school = [r for r in duplicate_rows if normalize(r["school"]) == school_norm]
    strong: list[tuple[dict[str, str], str]] = []
    review: list[tuple[dict[str, str], str, float]] = []

    for row in same_school:
        for alias in enterprise_aliases:
            kind, score = enterprise_match(alias, row["title"])
            if kind == "exact-substring":
                strong.append((row, alias))
                break
            if kind == "fuzzy-coverage":
                review.append((row, alias, score))
                break

    title_review: list[tuple[dict[str, str], float]] = []
    if args.title:
        proposed = normalize(args.title)
        for row in same_school:
            score = SequenceMatcher(None, proposed, normalize(row["title"])).ratio()
            if score >= 0.72:
                title_review.append((row, score))
        title_review.sort(key=lambda item: item[1], reverse=True)

    global_examples: list[dict[str, str]] = []
    for row in award_rows:
        if any(enterprise_match(alias, row["title"])[0] == "exact-substring" for alias in enterprise_aliases):
            global_examples.append(row)

    if strong:
        status = "BLOCK"
        exit_code = 2
    elif review or title_review:
        status = "REVIEW"
        exit_code = 1
    else:
        status = "CLEAR_IN_FILE"
        exit_code = 0

    print(f"STATUS: {status}")
    print("RULE SCOPE: same institution + same case enterprise within 2025-2026")
    print("BUNDLED DATA SCOPE: 2025 list; screening only, not final organizer clearance")
    print(f"SCHOOL: {args.school}")
    print(f"ENTERPRISE/ALIASES: {' | '.join(enterprise_aliases)}")
    print(f"SAME-SCHOOL RECORDS: {len(same_school)}")

    if strong:
        print("\nSame-school enterprise hits (strong warning):")
        for row, alias in strong[: args.top]:
            print(f"- [{row['year']}] alias={alias} | {row['title']}")
    if review:
        print("\nSame-school fuzzy hits (manual verification required):")
        for row, alias, score in sorted(review, key=lambda item: item[2], reverse=True)[: args.top]:
            print(f"- [{row['year']}] coverage={score:.0%} alias={alias} | {row['title']}")
    if title_review:
        print("\nSimilar same-school titles:")
        for row, score in title_review[: args.top]:
            print(f"- [{row['year']}] similarity={score:.0%} | {row['title']}")

    print("\nSame-school records for manual identity review (creative titles may omit the enterprise name):")
    if same_school:
        for row in same_school[: args.top]:
            print(f"- [{row['year']}] {row['title']}")
        if len(same_school) > args.top:
            print(f"- ... {len(same_school) - args.top} more; rerun with --top {len(same_school)}")
    else:
        print("- none found")

    print("\nGlobal award-title examples for this enterprise (informational only; not an automatic block):")
    if global_examples:
        for row in global_examples[: args.top]:
            print(f"- {row['award']} | {row['title']}")
    else:
        print("- none found")

    print(
        "\nNOTE: This is a screening result based on the bundled 2025 list. "
        "A creative title may not name its enterprise. Confirm aliases, every same-school record, "
        "and the latest official list with the school coordinator."
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
