#!/usr/bin/env python3
"""Validate a 20-slide, evidence-bound, ten-minute roadshow script."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(r"\[待|【】|待填写|TBD|XXX|Lorem", re.IGNORECASE)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
ALNUM_RE = re.compile(r"[A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)*")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*(?:%|亿元|万元|元|万|亿|家|个|项|次|页|秒|分钟|倍)?")
VALID_MODES = {"CREATE_FROM_APPROVED_DECK", "REVIEW_EXISTING_WITH_DECK"}
VALID_STATUSES = {"DRAFT", "REHEARSED", "APPROVED"}
VALID_RATE_STATUSES = {"UNCALIBRATED", "MEASURED"}
VALID_SUPPORT_STATUSES = {"SUPPORTED", "NEEDS_SOURCE", "REMOVE"}


def count_units(text: str) -> int:
    """Count one unit per CJK character or continuous alphanumeric token."""
    return len(CJK_RE.findall(text)) + len(ALNUM_RE.findall(text))


def is_real_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not PLACEHOLDER_RE.search(value)


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.search(value))
    if isinstance(value, list):
        return any(has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(has_placeholder(item) for item in value.values())
    return False


def nonempty_real_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(is_real_text(item) for item in value)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a 20-slide ten-minute roadshow script JSON."
    )
    parser.add_argument("script", type=Path, help="Path to the script JSON file")
    parser.add_argument(
        "--for-final",
        action="store_true",
        help="Apply final rehearsal, measured-rate, and team-approval gates",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def validate(data: dict[str, Any], for_final: bool) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    def error(message: str) -> None:
        errors.append(message)

    def warn(message: str) -> None:
        warnings.append(message)

    if data.get("mode") not in VALID_MODES:
        error(f"mode must be one of {sorted(VALID_MODES)}")
    if data.get("status") not in VALID_STATUSES:
        error(f"status must be one of {sorted(VALID_STATUSES)}")
    for field in (
        "script_version",
        "source_report_id",
        "source_report_version",
        "source_ppt_outline_version",
        "source_deck_id",
    ):
        if not is_real_text(data.get(field)):
            error(f"{field} must be filled with a non-placeholder value")
    if data.get("language") != "zh-CN":
        error("language must be zh-CN")
    if data.get("anonymous_check") is not True:
        error("anonymous_check must be true after checking school, names, logos, and contact details")
    if data.get("live_ai_use") is not False:
        error("live_ai_use must be false; live AI prompting is not allowed during presentation or Q&A")
    if data.get("hard_limit_seconds") != 600:
        error("hard_limit_seconds must equal the official 600-second limit")
    unsupported = data.get("unsupported_claims")
    if not isinstance(unsupported, list):
        error("unsupported_claims must be a list")
    elif unsupported:
        error("unsupported_claims must be empty; remove or source every unsupported claim")

    speakers = data.get("speakers")
    speaker_rates: dict[str, float] = {}
    speaker_rate_statuses: dict[str, str] = {}
    if not isinstance(speakers, list) or not speakers:
        error("speakers must contain at least one speaker")
    else:
        for index, speaker in enumerate(speakers, start=1):
            label = f"speakers[{index}]"
            if not isinstance(speaker, dict):
                error(f"{label} must be an object")
                continue
            name = speaker.get("name")
            if not is_real_text(name):
                error(f"{label}.name must be filled")
                continue
            if name in speaker_rates:
                error(f"duplicate speaker name: {name}")
                continue
            rate = speaker.get("rate_units_per_minute")
            if not isinstance(rate, (int, float)) or isinstance(rate, bool) or not 150 <= rate <= 360:
                error(f"{label}.rate_units_per_minute must be between 150 and 360")
                continue
            rate_status = speaker.get("rate_status")
            if rate_status not in VALID_RATE_STATUSES:
                error(f"{label}.rate_status must be one of {sorted(VALID_RATE_STATUSES)}")
                continue
            speaker_rates[name] = float(rate)
            speaker_rate_statuses[name] = rate_status

    slides = data.get("slides")
    total_seconds = 0.0
    total_units = 0
    total_capacity = 0.0
    used_speakers: list[str] = []
    if not isinstance(slides, list) or len(slides) != 20:
        error("slides must contain exactly 20 slide objects")
        slides = slides if isinstance(slides, list) else []

    for index, slide in enumerate(slides, start=1):
        label = f"slide {index}"
        if not isinstance(slide, dict):
            error(f"{label} must be an object")
            continue
        if slide.get("slide") != index:
            error(f"{label}.slide must equal {index}; slides must remain in order")
        for field in ("role", "slide_title", "must_say", "spoken_text", "stage_cue"):
            if not is_real_text(slide.get(field)):
                error(f"{label}.{field} must be filled with non-placeholder text")
        if index < 20 and not is_real_text(slide.get("transition")):
            error(f"{label}.transition must connect to the next slide")
        speaker = slide.get("speaker")
        if speaker not in speaker_rates:
            error(f"{label}.speaker must match a declared speaker")
        else:
            used_speakers.append(speaker)
        seconds = slide.get("seconds")
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds <= 0:
            error(f"{label}.seconds must be a positive number")
            seconds = 0
        total_seconds += float(seconds)
        sources = slide.get("source_locators")
        evidence_ids = slide.get("evidence_ids")
        if not isinstance(sources, list):
            error(f"{label}.source_locators must be a list")
            sources = []
        if not isinstance(evidence_ids, list):
            error(f"{label}.evidence_ids must be a list")
            evidence_ids = []
        if index > 1 and not (nonempty_real_list(sources) or nonempty_real_list(evidence_ids)):
            error(f"{label} needs at least one real report/PPT locator or evidence ID")
        support_status = slide.get("support_status")
        if support_status not in VALID_SUPPORT_STATUSES:
            error(f"{label}.support_status must be one of {sorted(VALID_SUPPORT_STATUSES)}")
        elif support_status != "SUPPORTED":
            error(f"{label}.support_status is {support_status}; source or remove the claim")
        emergency_cut = slide.get("emergency_cut")
        if not is_real_text(emergency_cut):
            message = f"{label}.emergency_cut is missing; mark one complete optional sentence"
            error(message) if for_final else warn(message)
        spoken_text = slide.get("spoken_text") if isinstance(slide.get("spoken_text"), str) else ""
        units = count_units(spoken_text)
        total_units += units
        if speaker in speaker_rates and seconds:
            capacity = speaker_rates[speaker] * float(seconds) / 60
            total_capacity += capacity
            if capacity and units > capacity * 1.08:
                message = f"{label} has {units} units for capacity {capacity:.0f}; shorten it"
                error(message) if for_final else warn(message)
            elif capacity and units < capacity * 0.65:
                warn(f"{label} uses only {units} of about {capacity:.0f} units; verify pacing and pauses")
        number_count = len(NUMBER_RE.findall(spoken_text))
        if number_count > 4:
            warn(f"{label} contains {number_count} numeric tokens; keep only 1–2 anchor numbers when possible")

    if total_seconds > 600:
        error(f"planned speaking time is {total_seconds:g}s, above the 600s hard limit")
    elif not 525 <= total_seconds <= 570:
        message = f"planned speaking time is {total_seconds:g}s; target 525–570s to preserve a 30–75s buffer"
        error(message) if for_final else warn(message)

    handoffs = sum(
        1 for previous, current in zip(used_speakers, used_speakers[1:]) if previous != current
    )
    if handoffs > 3:
        message = f"speaker handoffs total {handoffs}; maximum is 3"
        error(message) if for_final else warn(message)

    rehearsals = data.get("rehearsals")
    if not isinstance(rehearsals, list):
        error("rehearsals must be a list")
        rehearsals = []

    if for_final:
        if data.get("status") not in {"REHEARSED", "APPROVED"}:
            error("final validation requires status REHEARSED or APPROVED")
        for speaker in set(used_speakers):
            if speaker_rate_statuses.get(speaker) != "MEASURED":
                error(f"used speaker {speaker} must have rate_status MEASURED")
        if len(rehearsals) < 3:
            error("final validation requires at least three rehearsal records")
        else:
            final_three: list[float] = []
            for index, rehearsal in enumerate(rehearsals[-3:], start=len(rehearsals) - 2):
                if not isinstance(rehearsal, dict):
                    error(f"rehearsal {index} must be an object")
                    continue
                duration = rehearsal.get("total_seconds")
                if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
                    error(f"rehearsal {index}.total_seconds must be a positive number")
                    continue
                final_three.append(float(duration))
            if len(final_three) == 3:
                if any(duration > 600 for duration in final_three):
                    error(f"last three rehearsals must all be ≤600s; got {final_three}")
                median = statistics.median(final_three)
                if not 525 <= median <= 570:
                    error(f"last-three rehearsal median is {median:g}s; required range is 525–570s")
        approval = data.get("team_approval")
        if not isinstance(approval, dict) or approval.get("confirmed") is not True:
            error("team_approval.confirmed must be true for final validation")
        else:
            if approval.get("confirmed_version") != data.get("script_version"):
                error("team_approval.confirmed_version must equal script_version")
            if not is_real_text(approval.get("confirmed_at")):
                error("team_approval.confirmed_at must be filled")

    if has_placeholder(data):
        error("document still contains placeholder text such as [待填写], TBD, or XXX")

    summary = {
        "slides": len(slides),
        "seconds": total_seconds,
        "units": total_units,
        "capacity": total_capacity,
        "handoffs": handoffs,
    }
    return errors, warnings, summary


def main() -> int:
    args = parse_args()
    try:
        data = load_json(args.script)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings, summary = validate(data, args.for_final)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(
            f"INVALID: {len(errors)} error(s), {len(warnings)} warning(s) | "
            f"{summary['slides']} slides | {summary['seconds']:g}s | "
            f"{summary['units']} units | {summary['handoffs']} handoffs",
            file=sys.stderr,
        )
        return 1
    print(
        f"VALID: {summary['slides']}-slide script | {summary['seconds']:g}s | "
        f"{summary['units']} units / {summary['capacity']:.0f} estimated capacity | "
        f"{summary['handoffs']} handoffs | {len(warnings)} warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
