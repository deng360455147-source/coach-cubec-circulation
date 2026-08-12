#!/usr/bin/env python3
"""Validate the fixed competition report framework and its evidence labels."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXPECTED_TOP_LEVEL = [
    ("1", "目录"),
    ("2", "概要"),
    ("3", "引言"),
    ("4", "案例简介"),
    ("5", "企业内部及外部分析"),
    ("6", "发展瓶颈"),
    ("7", "结论与启示"),
    ("8", "附录及参考资料"),
]

EXPECTED_CORE_DIMENSIONS = [
    ("5.2", "企业战略"),
    ("5.3", "商业模式"),
    ("5.4", "运营管理"),
    ("5.5", "市场竞争"),
    ("5.6", "财务状况"),
]

STATUS_PATTERN = re.compile(
    r"^\s*\[(结构项|待调研|待核验|待验证假设|团队判断|已核验:(E[A-Za-z0-9_-]+))\]"
)
PLACEHOLDER_PATTERN = re.compile(r"【\s*】|【待提供】|\[待提供\]|待提供|待核验|待调研")
LOCATOR_PATTERN = re.compile(r"页|p\.|章节|表|图|行|URL|https?://|文件|记录|台账", re.IGNORECASE)


def between(text: str, start: str, end: str, label: str, errors: list[str]) -> str:
    if start not in text or end not in text:
        errors.append(f"缺少 {label} 标记：{start} / {end}")
        return ""
    body = text.split(start, 1)[1].split(end, 1)[0]
    if not body.strip():
        errors.append(f"{label} 为空")
    return body


def section_chunks(directory: str) -> list[tuple[int, str, str]]:
    heading_re = re.compile(r"^(###|####)\s+([^\n]+)$", re.MULTILINE)
    matches = list(heading_re.finditer(directory))
    chunks: list[tuple[int, str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(directory)
        chunks.append((level, title, directory[match.end() : end]))
    return chunks


def validate_claim_field(title: str, chunk: str, errors: list[str]) -> None:
    claim_match = re.search(
        r"^- 可写主张（必须带状态）[：:]\s*(.+)$", chunk, re.MULTILINE
    )
    if not claim_match:
        errors.append(f"“{title}”缺少“可写主张（必须带状态）”字段")
        return

    claim = claim_match.group(1).strip()
    status_match = STATUS_PATTERN.match(claim)
    if not status_match:
        errors.append(f"“{title}”的可写主张未以允许的状态标签开头：{claim}")
        return

    evidence_id = status_match.group(2)
    if evidence_id:
        locator_match = re.search(
            r"^- 证据 ID / 精确定位[：:]\s*(.+)$", chunk, re.MULTILINE
        )
        locator = locator_match.group(1).strip() if locator_match else ""
        if not locator or PLACEHOLDER_PATTERN.search(locator):
            errors.append(f"“{title}”标记为已核验，但证据定位为空或仍是占位符")
        elif evidence_id not in locator:
            errors.append(f"“{title}”的已核验证据 ID {evidence_id} 未出现在精确定位字段")
        elif not LOCATOR_PATTERN.search(locator):
            errors.append(f"“{title}”的已核验证据缺少页码、章节、URL、文件或调研记录等定位")


def validate_register(register: str, errors: list[str]) -> None:
    rows = [line for line in register.splitlines() if line.strip().startswith("|")]
    data_rows: list[list[str]] = []
    for line in rows:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] == "主张 ID" or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        data_rows.append(cells)

    for row_number, cells in enumerate(data_rows, start=1):
        if len(cells) != 7:
            errors.append(f"主张—证据登记表第 {row_number} 条不是 7 列")
            continue
        status_match = STATUS_PATTERN.fullmatch(cells[3])
        if not status_match:
            errors.append(f"主张—证据登记表第 {row_number} 条状态无效：{cells[3]}")
            continue
        evidence_id = status_match.group(2)
        if evidence_id:
            if PLACEHOLDER_PATTERN.search(cells[4]) or PLACEHOLDER_PATTERN.search(cells[5]):
                errors.append(f"主张—证据登记表第 {row_number} 条标记为已核验，但证据 ID 或定位仍是占位符")
            elif evidence_id not in cells[4]:
                errors.append(f"主张—证据登记表第 {row_number} 条缺少已核验证据 ID {evidence_id}")
            elif not LOCATOR_PATTERN.search(cells[5]):
                errors.append(f"主张—证据登记表第 {row_number} 条缺少可复核的精确定位")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"无法读取 UTF-8 Markdown：{exc}"]

    directory = between(
        text,
        "<!-- REPORT_DIRECTORY_START -->",
        "<!-- REPORT_DIRECTORY_END -->",
        "固定一级目录",
        errors,
    )
    register = between(
        text,
        "<!-- CLAIM_REGISTER_START -->",
        "<!-- CLAIM_REGISTER_END -->",
        "主张—证据登记表",
        errors,
    )

    if directory:
        chunks = section_chunks(directory)
        top_level: list[tuple[str, str]] = []
        for level, title, _ in chunks:
            if level != 3:
                continue
            match = re.fullmatch(r"(\d+)\.\s+(.+)", title)
            if match:
                top_level.append((match.group(1), match.group(2).strip()))
        if top_level != EXPECTED_TOP_LEVEL:
            errors.append(
                "固定一级目录不合格：必须且只能依次为 “"
                + "、".join(f"{number}. {name}" for number, name in EXPECTED_TOP_LEVEL)
                + f"”；当前为 {top_level}"
            )

        fifth_start = directory.find("### 5. 企业内部及外部分析")
        sixth_start = directory.find("### 6. 发展瓶颈")
        fifth = directory[fifth_start:sixth_start] if fifth_start >= 0 and sixth_start > fifth_start else ""
        core_found: list[tuple[str, str]] = []
        for match in re.finditer(r"^####\s+(5\.\d+)\s+(.+)$", fifth, re.MULTILINE):
            pair = (match.group(1), match.group(2).strip())
            if pair in EXPECTED_CORE_DIMENSIONS:
                core_found.append(pair)
        if core_found != EXPECTED_CORE_DIMENSIONS:
            errors.append(
                "第 5 项未按顺序完整覆盖五个核心经营维度："
                + "、".join(name for _, name in EXPECTED_CORE_DIMENSIONS)
                + f"；当前识别为 {core_found}"
            )

        required_titles = {f"{number}. {name}" for number, name in EXPECTED_TOP_LEVEL}
        required_titles.update(f"{number} {name}" for number, name in EXPECTED_CORE_DIMENSIONS)
        chunk_map = {title: chunk for _, title, chunk in chunks}
        for title in sorted(required_titles):
            chunk = chunk_map.get(title)
            if chunk is None:
                errors.append(f"缺少必检章节：{title}")
            else:
                validate_claim_field(title, chunk, errors)

    if register:
        validate_register(register, errors)

    if "`UNSUPPORTED_CLAIMS = 0`" not in text:
        errors.append("缺少不支持主张声明：`UNSUPPORTED_CLAIMS = 0`")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验流通业经营模拟赛道分析报告框架确认单的固定结构与证据状态。"
    )
    parser.add_argument("framework", type=Path, help="待校验的 Markdown 确认单")
    args = parser.parse_args()

    errors = validate(args.framework)
    if errors:
        print("FAIL: 分析报告框架确认单未通过校验")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: 固定 8 项、五个核心经营维度与证据状态均通过结构校验")
    return 0


if __name__ == "__main__":
    sys.exit(main())
