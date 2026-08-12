#!/usr/bin/env python3
"""Validate the evidence and timing contract for a 20-slide outline."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VALID_INPUT_MODES = {"CONVERSATION_REPORT", "UPLOADED_REPORT"}
VALID_SUPPORT = {"SUPPORTED", "NEEDS_REPORT_EVIDENCE", "REMOVE"}
VALID_STATUSES = {"DRAFT", "APPROVED"}
GENERIC_TITLES = {
    "行业分析",
    "内部分析",
    "外部分析",
    "swot",
    "swot分析",
    "解决方案",
    "谢谢",
    "thank you",
}
PLACEHOLDER_RE = re.compile(r"\[待|【】|待填写|lorem|单击此处|工作计划/工作总结/年终汇报", re.I)
REQUIRED_SLIDE_KEYS = {
    "slide",
    "role",
    "title",
    "claim",
    "source_locators",
    "evidence_ids",
    "visual",
    "speaker_job",
    "seconds",
    "evidence_required",
    "support_status",
}


def has_real_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and not PLACEHOLDER_RE.search(value)
    if isinstance(value, list):
        return any(has_real_value(item) for item in value)
    return value is not None


def validate(data: Any, *, for_production: bool = False) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    total_seconds = 0

    if not isinstance(data, dict):
        return ["顶层必须是 JSON 对象"], warnings, total_seconds

    if data.get("input_mode") not in VALID_INPUT_MODES:
        errors.append("input_mode 必须是 CONVERSATION_REPORT 或 UPLOADED_REPORT")
    if data.get("status") not in VALID_STATUSES:
        errors.append("status 必须是 DRAFT 或 APPROVED")
    for field in ("outline_version", "source_report_id", "source_report_version"):
        if not has_real_value(data.get(field)):
            errors.append(f"{field} 未锁定")
    if data.get("anonymous_check") is not True:
        errors.append("anonymous_check 必须为 true")
    if data.get("unsupported_claims"):
        errors.append("unsupported_claims 必须清零后才能通过")

    approval = data.get("user_approval")
    if not isinstance(approval, dict):
        errors.append("user_approval 必须是对象")
        approval = {}
    if for_production:
        if data.get("status") != "APPROVED":
            errors.append("制作前 status 必须为 APPROVED")
        if approval.get("confirmed") is not True:
            errors.append("制作前必须记录 user_approval.confirmed=true")
        if approval.get("confirmed_version") != data.get("outline_version"):
            errors.append("confirmed_version 必须与 outline_version 一致")
        if not has_real_value(approval.get("confirmed_at")):
            errors.append("制作前必须记录 confirmed_at")

    slides = data.get("slides")
    if not isinstance(slides, list):
        return errors + ["slides 必须是数组"], warnings, total_seconds
    if len(slides) != 20:
        errors.append(f"slides 必须恰好20页，当前为{len(slides)}页")

    numbers: list[int] = []
    for index, slide in enumerate(slides, start=1):
        prefix = f"第 {index} 项"
        if not isinstance(slide, dict):
            errors.append(f"{prefix} 不是对象")
            continue
        missing = sorted(REQUIRED_SLIDE_KEYS - slide.keys())
        if missing:
            errors.append(f"{prefix} 缺少字段：{', '.join(missing)}")
            continue

        number = slide.get("slide")
        if not isinstance(number, int):
            errors.append(f"{prefix} slide 必须是整数")
        else:
            numbers.append(number)

        for field in ("role", "title", "claim", "visual", "speaker_job"):
            if not has_real_value(slide.get(field)):
                errors.append(f"第 {number or index} 页 {field} 为空或仍含占位符")

        title = str(slide.get("title", "")).strip().lower()
        if title in GENERIC_TITLES:
            errors.append(f"第 {number or index} 页标题过于目录化：{slide.get('title')}")

        seconds = slide.get("seconds")
        if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds <= 0:
            errors.append(f"第 {number or index} 页 seconds 必须是正整数")
        else:
            total_seconds += seconds

        support = slide.get("support_status")
        if support not in VALID_SUPPORT:
            errors.append(f"第 {number or index} 页 support_status 无效")
        elif support != "SUPPORTED":
            errors.append(f"第 {number or index} 页尚未被报告支持：{support}")

        evidence_required = slide.get("evidence_required")
        expected_evidence_required = number != 1
        if evidence_required is not expected_evidence_required:
            errors.append(
                f"第 {number or index} 页 evidence_required 必须为 "
                f"{str(expected_evidence_required).lower()}"
            )

        locators = slide.get("source_locators")
        evidence = slide.get("evidence_ids")
        if not isinstance(locators, list) or not isinstance(evidence, list):
            errors.append(f"第 {number or index} 页来源定位和证据 ID 必须是数组")
        elif expected_evidence_required:
            if not has_real_value(locators) and not has_real_value(evidence):
                errors.append(f"第 {number or index} 页缺少报告定位或证据 ID")

    if numbers != list(range(1, 21)):
        errors.append("页码必须按1–20连续且与数组顺序一致")
    if total_seconds > 600:
        errors.append(f"口播预算 {total_seconds} 秒，超过 600 秒硬上限")
    elif not 525 <= total_seconds <= 570:
        message = f"口播预算 {total_seconds} 秒，不在建议的 525–570 秒彩排区间"
        if for_production:
            errors.append(message)
        else:
            warnings.append(message)

    return errors, warnings, total_seconds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--for-production",
        action="store_true",
        help="require explicit user approval and production-ready timing",
    )
    parser.add_argument("outline", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.outline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: 无法读取 JSON：{exc}", file=sys.stderr)
        return 2

    errors, warnings, total_seconds = validate(data, for_production=args.for_production)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"INVALID: {len(errors)} 个问题", file=sys.stderr)
        return 1

    print(f"VALID: 20-slide outline | {total_seconds}s | buffer {600 - total_seconds}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
