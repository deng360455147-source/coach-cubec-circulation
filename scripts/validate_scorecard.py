#!/usr/bin/env python3
"""Validate a circulation case-report scorecard without external dependencies."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


EXPECTED = {
    "framework": ("分析框架", 20),
    "object": ("分析对象", 10),
    "perspective": ("分析视角", 10),
    "method": ("分析方法", 10),
    "conclusion": ("分析结论", 10),
}
REVIEW_STATUSES = {"SCORABLE", "PROVISIONAL", "UNSCORABLE"}
SOURCE_STATUSES = {"REPORT_ONLY", "PARTIALLY_VERIFIED", "EVIDENCE_VERIFIED"}
CALIBRATION_STATUSES = {"RULE_BASED_ONLY", "PARTIALLY_CALIBRATED", "HUMAN_CALIBRATED"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
CLAIM_STATUSES = {"R", "V", "I", "M"}
DIAGNOSTIC_IDS = {
    "regional_causality",
    "central_contradiction",
    "success_bottleneck_dual_line",
    "method_serves_question",
    "bottleneck_solution_mirror",
    "decision_charts",
    "reproducible_appendix",
}
DIAGNOSTIC_STATUSES = {"MATURE", "PARTIAL", "MISSING", "UNABLE_TO_JUDGE"}


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def half_step(value: float) -> bool:
    return abs(value * 2 - round(value * 2)) < 1e-9


def validate_evidence(items: object, path: str, allowed_statuses: set[str], errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append(f"{path} must be a list")
        return
    for i, item in enumerate(items):
        item_path = f"{path}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        for field in ("locator", "summary", "claim_status"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{item_path}.{field} must be a non-empty string")
        if item.get("claim_status") not in allowed_statuses:
            errors.append(f"{item_path}.claim_status must be one of {sorted(allowed_statuses)}")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read valid JSON: {exc}"]

    report = data.get("report")
    if not isinstance(report, dict):
        return ["report must be an object"]
    review_status = report.get("review_status")
    source_status = report.get("source_verification")
    for field in ("id", "version", "input_type", "rubric_version"):
        if not isinstance(report.get(field), str) or not report[field].strip():
            errors.append(f"report.{field} must be a non-empty string")
    if review_status not in REVIEW_STATUSES:
        errors.append(f"report.review_status must be one of {sorted(REVIEW_STATUSES)}")
    if source_status not in SOURCE_STATUSES:
        errors.append(f"report.source_verification must be one of {sorted(SOURCE_STATUSES)}")
    if report.get("calibration_status") not in CALIBRATION_STATUSES:
        errors.append(f"report.calibration_status must be one of {sorted(CALIBRATION_STATUSES)}")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, list):
        return errors + ["dimensions must be a list"]
    by_id: dict[str, dict] = {}
    for index, dimension in enumerate(dimensions):
        if not isinstance(dimension, dict):
            errors.append(f"dimensions[{index}] must be an object")
            continue
        dim_id = dimension.get("id")
        if dim_id in by_id:
            errors.append(f"duplicate dimension id: {dim_id}")
        elif isinstance(dim_id, str):
            by_id[dim_id] = dimension
        else:
            errors.append(f"dimensions[{index}].id must be a string")

    if set(by_id) != set(EXPECTED):
        errors.append(f"dimension ids must be exactly {sorted(EXPECTED)}")

    working_scores: list[float] = []
    lower_scores: list[float] = []
    upper_scores: list[float] = []
    low_count = 0

    for dim_id, (expected_name, max_score) in EXPECTED.items():
        dimension = by_id.get(dim_id)
        if not dimension:
            continue
        prefix = f"dimensions[{dim_id}]"
        if dimension.get("name") != expected_name:
            errors.append(f"{prefix}.name must be {expected_name!r}")
        if dimension.get("max_score") != max_score:
            errors.append(f"{prefix}.max_score must be {max_score}")
        confidence = dimension.get("confidence")
        if confidence not in CONFIDENCE:
            errors.append(f"{prefix}.confidence must be one of {sorted(CONFIDENCE)}")
        if confidence == "LOW":
            low_count += 1

        validate_evidence(
            dimension.get("supporting_evidence"),
            f"{prefix}.supporting_evidence",
            {"R", "V"},
            errors,
        )
        validate_evidence(
            dimension.get("contrary_or_missing"),
            f"{prefix}.contrary_or_missing",
            {"I", "M"},
            errors,
        )

        values = [dimension.get(key) for key in ("pass_a", "pass_b", "working_score")]
        score_range = dimension.get("score_range")
        if review_status == "UNSCORABLE":
            if any(value is not None for value in values) or score_range is not None:
                errors.append(f"{prefix} scores and range must be null when UNSCORABLE")
            continue

        if not all(is_number(value) for value in values):
            errors.append(f"{prefix} pass_a, pass_b, and working_score must be finite numbers")
            continue
        pass_a, pass_b, working = (float(value) for value in values)
        if not all(0 <= value <= max_score for value in (pass_a, pass_b, working)):
            errors.append(f"{prefix} scores must be between 0 and {max_score}")
        if not all(half_step(value) for value in (pass_a, pass_b, working)):
            errors.append(f"{prefix} scores must use 0.5-point increments")
        if not (isinstance(score_range, list) and len(score_range) == 2 and all(is_number(v) for v in score_range)):
            errors.append(f"{prefix}.score_range must contain two finite numbers")
            continue
        lower, upper = map(float, score_range)
        if not (0 <= lower <= working <= upper <= max_score):
            errors.append(f"{prefix}.score_range must satisfy 0 <= lower <= working <= upper <= {max_score}")
        if not half_step(lower) or not half_step(upper):
            errors.append(f"{prefix}.score_range must use 0.5-point increments")
        threshold = 2 if dim_id == "framework" else 1
        if abs(pass_a - pass_b) > threshold and confidence != "LOW":
            errors.append(f"{prefix}.confidence must be LOW when pass disagreement exceeds {threshold}")
        if working > 0 and not dimension.get("supporting_evidence"):
            errors.append(f"{prefix} needs supporting evidence for a positive score")
        ceiling = dimension.get("ceiling_applied")
        if ceiling is not None:
            if not isinstance(ceiling, dict) or not is_number(ceiling.get("max_working_score")) or not isinstance(ceiling.get("reason"), str):
                errors.append(f"{prefix}.ceiling_applied must be null or contain max_working_score and reason")
            else:
                ceiling_score = float(ceiling["max_working_score"])
                if not ceiling["reason"].strip():
                    errors.append(f"{prefix}.ceiling_applied.reason must be non-empty")
                if not 0 <= ceiling_score <= max_score:
                    errors.append(f"{prefix}.ceiling_applied.max_working_score must be between 0 and {max_score}")
                if working > ceiling_score or upper > ceiling_score:
                    errors.append(f"{prefix} working score and range upper bound must not exceed applied ceiling")

        working_scores.append(working)
        lower_scores.append(lower)
        upper_scores.append(upper)

    total = data.get("total")
    if not isinstance(total, dict):
        errors.append("total must be an object")
    else:
        if total.get("max_score") != 60:
            errors.append("total.max_score must be 60")
        total_confidence = total.get("confidence")
        if total_confidence not in CONFIDENCE:
            errors.append(f"total.confidence must be one of {sorted(CONFIDENCE)}")
        if source_status == "REPORT_ONLY" and total_confidence == "HIGH":
            errors.append("total.confidence cannot be HIGH when source_verification is REPORT_ONLY")
        if review_status == "PROVISIONAL" and total_confidence == "HIGH":
            errors.append("total.confidence cannot be HIGH when review_status is PROVISIONAL")
        if low_count >= 2 and total_confidence != "LOW":
            errors.append("total.confidence must be LOW when two or more dimensions are LOW")

        if review_status == "UNSCORABLE":
            if total.get("working_score") is not None or total.get("score_range") is not None:
                errors.append("total scores and range must be null when UNSCORABLE")
        elif len(working_scores) == 5:
            expected_working = sum(working_scores)
            expected_lower = sum(lower_scores)
            expected_upper = sum(upper_scores)
            if not is_number(total.get("working_score")) or abs(float(total["working_score"]) - expected_working) > 1e-9:
                errors.append(f"total.working_score must equal {expected_working:g}")
            score_range = total.get("score_range")
            if not (isinstance(score_range, list) and len(score_range) == 2 and all(is_number(v) for v in score_range)):
                errors.append("total.score_range must contain two finite numbers")
            elif abs(float(score_range[0]) - expected_lower) > 1e-9 or abs(float(score_range[1]) - expected_upper) > 1e-9:
                errors.append(f"total.score_range must equal [{expected_lower:g}, {expected_upper:g}]")

    diagnostics = data.get("national_first_diagnostics")
    if not isinstance(diagnostics, list):
        errors.append("national_first_diagnostics must be a list")
    elif review_status != "UNSCORABLE":
        diagnostic_ids: set[str] = set()
        for index, item in enumerate(diagnostics):
            prefix = f"national_first_diagnostics[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            diagnostic_id = item.get("id")
            if not isinstance(diagnostic_id, str):
                errors.append(f"{prefix}.id must be a string")
            elif diagnostic_id in diagnostic_ids:
                errors.append(f"duplicate national-first diagnostic id: {diagnostic_id}")
            else:
                diagnostic_ids.add(diagnostic_id)
            if item.get("status") not in DIAGNOSTIC_STATUSES:
                errors.append(f"{prefix}.status must be one of {sorted(DIAGNOSTIC_STATUSES)}")
            if not isinstance(item.get("locator"), str) or not item["locator"].strip():
                errors.append(f"{prefix}.locator must be a non-empty string")
            if not isinstance(item.get("impacts"), list) or not all(value in EXPECTED for value in item.get("impacts", [])):
                errors.append(f"{prefix}.impacts must contain only official dimension ids")
        if diagnostic_ids != DIAGNOSTIC_IDS:
            errors.append(f"national-first diagnostic ids must be exactly {sorted(DIAGNOSTIC_IDS)}")

    for field in ("blocking_items", "unverified_claims"):
        if not isinstance(data.get(field), list):
            errors.append(f"{field} must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scorecard", type=Path)
    args = parser.parse_args()
    errors = validate(args.scorecard)
    if errors:
        print("Scorecard validation: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Scorecard validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
