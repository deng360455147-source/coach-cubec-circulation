#!/usr/bin/env python3
"""Validate the fixed three-level CUBEC circulation report framework."""

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
    ("5", "企业内部分析"),
    ("6", "企业外部分析"),
    ("7", "企业经营模式"),
    ("8", "发展瓶颈"),
    ("9", "经营优化方案"),
    ("10", "结论与启示"),
    ("11", "附录及参考资料"),
]

REQUIRED_SECOND_LEVEL = {
    "1.1": "目录编排",
    "2.1": "研究对象与核心问题",
    "2.2": "主要结论与方案方向",
    "3.1": "研究背景与选题价值",
    "3.2": "研究设计与范围",
    "4.1": "企业与业务概况",
    "4.2": "目标地区与案例价值",
    "5.1": "企业战略",
    "5.2": "运营管理",
    "5.3": "财务状况",
    "6.1": "宏观与地区环境",
    "6.2": "行业与市场演进",
    "6.3": "市场竞争",
    "7.1": "商业模式",
    "7.2": "流通价值链与经营机制",
    "7.3": "地区适配与扩张机制",
    "10.1": "研究结论",
    "10.2": "企业与行业启示",
    "10.3": "适用边界与研究局限",
    "11.1": "企业重要数据概览",
    "11.2": "调查问卷",
    "11.3": "访谈纲要（含知情说明与编码）",
    "11.4": "参考文献",
    "11.5": "观察/竞品与现场记录",
    "11.6": "补充图表与地区对标",
}

CORE_DIMENSIONS = {
    "5.1": "企业战略",
    "5.2": "运营管理",
    "5.3": "财务状况",
    "6.3": "市场竞争",
    "7.1": "商业模式",
}

REQUIRED_TERTIARY = {
    "1.1.1": "章节层级与页码索引",
    "2.1.1": "案例对象、目标地区与研究问题",
    "2.2.1": "核心发现、发展瓶颈与对应方案",
    "3.1.1": "背景与选题价值",
    "3.1.2": "研究问题与目标",
    "3.2.1": "数据来源与分析方法",
    "3.2.2": "研究范围、创新与局限",
    "4.1.1": "企业定位与关键发展节点",
    "4.1.2": "核心业务与经营布局",
    "4.2.1": "目标地区经营基础",
    "4.2.2": "企业优势与案例价值",
    "5.1.1": "战略定位与增长路径",
    "5.1.2": "资源、组织与执行能力",
    "5.1.3": "地区战略与阶段重点",
    "5.2.1": "产品、渠道与客户运营",
    "5.2.2": "采购、供应链与伙伴协同",
    "5.2.3": "仓配履约、库存与质量效率",
    "5.3.1": "收入、利润与成本结构",
    "5.3.2": "现金、周转与资本效率",
    "5.3.3": "单位经济、代理指标与局限",
    "6.1.1": "政策与制度环境",
    "6.1.2": "经济、人口与社会文化环境",
    "6.1.3": "技术、基础设施与地理条件",
    "6.2.1": "行业规模、阶段与趋势",
    "6.2.2": "顾客、场景与渠道变化",
    "6.2.3": "供应生态与流通链变化",
    "6.3.1": "竞争者、替代方案与竞争边界",
    "6.3.2": "同口径竞争对标与企业位置",
    "6.3.3": "竞争压力、外部机会与经营影响",
    "7.1.1": "顾客、场景与价值主张",
    "7.1.2": "渠道、关系与价值交付",
    "7.1.3": "收入成本、伙伴与价值获取",
    "7.2.1": "采购供应与前端需求连接",
    "7.2.2": "商品、信息与资金流协同",
    "7.2.3": "价值创造、价值泄漏与关键杠杆",
    "7.3.1": "全国标准与地方经营接口",
    "7.3.2": "目标地区适配动作与差距",
    "7.3.3": "复制、规模化与边界条件",
    "10.1.1": "研究问题逐项回答",
    "10.1.2": "优势、错配与瓶颈机制",
    "10.1.3": "方案价值与验证结论",
    "10.2.1": "对案例企业的经营启示",
    "10.2.2": "对目标地区流通业的启示",
    "10.2.3": "对同类企业的可迁移启示",
    "10.3.1": "适用条件与不可复制条件",
    "10.3.2": "数据、样本与方法局限",
    "10.3.3": "后续研究与验证计划",
    "11.1.1": "核心经营数据与口径说明",
    "11.2.1": "问卷正文与选项",
    "11.2.2": "发放回收、样本结构与质量控制",
    "11.3.1": "访谈纲要与对象说明",
    "11.3.2": "知情说明、匿名规则与编码",
    "11.4.1": "政策、统计与企业资料",
    "11.4.2": "学术、行业、媒体与网络资料",
    "11.5.1": "观察与现场记录",
    "11.5.2": "竞品选择与对标记录",
    "11.6.1": "补充图表",
    "11.6.2": "地区对标与口径说明",
}

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
    heading_re = re.compile(r"^(###|####|#####)\s+([^\n]+)$", re.MULTILINE)
    matches = list(heading_re.finditer(directory))
    chunks: list[tuple[int, str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(directory)
        chunks.append((level, title, directory[match.end() : end]))
    return chunks


def numbered_title(title: str, levels: int) -> tuple[str, str] | None:
    number_pattern = r"\d+" + r"\.\d+" * (levels - 1)
    match = re.fullmatch(rf"({number_pattern})\.?\s+(.+)", title)
    if not match:
        return None
    return match.group(1), match.group(2).strip()


def title_matches(actual: str, expected: str) -> bool:
    return actual == expected or actual.startswith(expected + "：") or actual.startswith(expected + "（")


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
        validate_verified_locator(title, evidence_id, locator, errors)


def validate_verified_locator(title: str, evidence_id: str, locator: str, errors: list[str]) -> None:
    if not locator or PLACEHOLDER_PATTERN.search(locator):
        errors.append(f"“{title}”标记为已核验，但证据定位为空或仍是占位符")
    elif evidence_id not in locator:
        errors.append(f"“{title}”的已核验证据 ID {evidence_id} 未出现在证据与边界/定位字段")
    elif not LOCATOR_PATTERN.search(locator):
        errors.append(f"“{title}”的已核验证据缺少页码、章节、URL、文件或调研记录等定位")


def validate_tertiary_summary(title: str, chunk: str, errors: list[str]) -> None:
    summary_lines = re.findall(
        r"^- (内容概括|证据与边界|输出衔接)[：:]\s*(.+)$", chunk, re.MULTILINE
    )
    if not 2 <= len(summary_lines) <= 3:
        errors.append(f"“{title}”下必须有 2—3 行概括；当前识别到 {len(summary_lines)} 行")
        return
    fields = [field for field, _ in summary_lines]
    if fields.count("内容概括") != 1 or fields.count("证据与边界") != 1:
        errors.append(f"“{title}”必须各有一行“内容概括”和“证据与边界”")
        return
    values = {field: value.strip() for field, value in summary_lines}
    for field in ("内容概括", "证据与边界"):
        if not STATUS_PATTERN.match(values[field]):
            errors.append(f"“{title}”的“{field}”未以允许的状态标签开头")
    content_match = STATUS_PATTERN.match(values["内容概括"])
    boundary_match = STATUS_PATTERN.match(values["证据与边界"])
    evidence_ids = [
        match.group(2)
        for match in (content_match, boundary_match)
        if match is not None and match.group(2)
    ]
    for evidence_id in set(evidence_ids):
        validate_verified_locator(title, evidence_id, values["证据与边界"], errors)


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


def validate_fixed_number_sets(
    parsed: dict[int, dict[str, tuple[str, str]]], errors: list[str]
) -> None:
    for chapter in ("1", "2", "3", "4", "5", "6", "7", "10", "11"):
        expected_second = {
            number for number in REQUIRED_SECOND_LEVEL if number.split(".")[0] == chapter
        }
        actual_second = {
            number for number in parsed[4] if number.split(".")[0] == chapter
        }
        if actual_second != expected_second:
            errors.append(
                f"第 {chapter} 章二级标题数量或编号不合格："
                f"应为 {sorted(expected_second)}，当前为 {sorted(actual_second)}"
            )

        expected_third = {
            number for number in REQUIRED_TERTIARY if number.split(".")[0] == chapter
        }
        actual_third = {
            number for number in parsed[5] if number.split(".")[0] == chapter
        }
        if actual_third != expected_third:
            errors.append(
                f"第 {chapter} 章三级标题数量或编号不合格："
                f"应为 {sorted(expected_third)}，当前为 {sorted(actual_third)}"
            )


def validate_result_items(
    parsed: dict[int, dict[str, tuple[str, str]]],
    chapter: str,
    count: int,
    tertiary_names: tuple[str, str, str],
    prohibited_terms: tuple[str, ...],
    label: str,
    errors: list[str],
) -> None:
    expected_second = {f"{chapter}.{index}" for index in range(1, count + 1)}
    actual_second = {
        number for number in parsed[4] if number.split(".")[0] == chapter
    }
    if actual_second != expected_second:
        errors.append(
            f"{label}二级标题必须按顺序连续编号："
            f"应为 {sorted(expected_second)}，当前为 {sorted(actual_second)}"
        )

    expected_third: set[str] = set()
    for index in range(1, count + 1):
        second_number = f"{chapter}.{index}"
        second_item = parsed[4].get(second_number)
        if second_item and any(term in second_item[0] for term in prohibited_terms):
            errors.append(f"{label}二级标题“{second_item[0]}”过于抽象，必须直接概括结果")
        for position, expected_name in enumerate(tertiary_names, start=1):
            number = f"{second_number}.{position}"
            expected_third.add(number)
            item = parsed[5].get(number)
            if item is None:
                errors.append(f"缺少{label}三级标题：{number} {expected_name}")
            elif not title_matches(item[0], expected_name):
                errors.append(f"{label}三级标题 {number} 应为“{expected_name}”，当前为“{item[0]}”")

    actual_third = {
        number for number in parsed[5] if number.split(".")[0] == chapter
    }
    if actual_third != expected_third:
        errors.append(
            f"{label}三级标题数量或编号不合格："
            f"应为 {sorted(expected_third)}，当前为 {sorted(actual_third)}"
        )


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
        "固定三级框架",
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
        parsed: dict[int, dict[str, tuple[str, str]]] = {3: {}, 4: {}, 5: {}}
        ordered_top: list[tuple[str, str]] = []
        for level, title, chunk in chunks:
            result = numbered_title(title, level - 2)
            if result is None:
                continue
            number, name = result
            parsed[level][number] = (name, chunk)
            if level == 3:
                ordered_top.append((number, name))

        if ordered_top != EXPECTED_TOP_LEVEL:
            errors.append(
                "固定一级目录不合格：必须且只能依次为 “"
                + "、".join(f"{number}. {name}" for number, name in EXPECTED_TOP_LEVEL)
                + f"”；当前为 {ordered_top}"
            )

        for number, name in EXPECTED_TOP_LEVEL:
            item = parsed[3].get(number)
            if item is None:
                errors.append(f"缺少一级章节：{number}. {name}")
            elif item[0] != name:
                errors.append(f"一级章节 {number} 应为“{name}”，当前为“{item[0]}”")
            else:
                validate_claim_field(f"{number}. {name}", item[1], errors)

        for number, expected in REQUIRED_SECOND_LEVEL.items():
            item = parsed[4].get(number)
            if item is None:
                errors.append(f"缺少固定二级标题：{number} {expected}")
            elif not title_matches(item[0], expected):
                errors.append(f"二级标题 {number} 应为“{expected}”，当前为“{item[0]}”")

        for number, expected in CORE_DIMENSIONS.items():
            item = parsed[4].get(number)
            if item is None or not title_matches(item[0], expected):
                errors.append(f"核心经营维度“{expected}”未固定落在 {number}")

        for number, expected in REQUIRED_TERTIARY.items():
            item = parsed[5].get(number)
            if item is None:
                errors.append(f"缺少固定三级标题：{number} {expected}")
            elif not title_matches(item[0], expected):
                errors.append(f"三级标题 {number} 应为“{expected}”，当前为“{item[0]}”")

        chapter_three_start = directory.find("### 3. 引言")
        chapter_four_start = directory.find("### 4. 案例简介")
        chapter_five_start = directory.find("### 5. 企业内部分析")
        chapter_three = (
            directory[chapter_three_start:chapter_four_start]
            if chapter_three_start >= 0 and chapter_four_start > chapter_three_start
            else ""
        )
        chapter_four = (
            directory[chapter_four_start:chapter_five_start]
            if chapter_four_start >= 0 and chapter_five_start > chapter_four_start
            else ""
        )
        if "研究框架图" not in chapter_three:
            errors.append("第3章引言必须在三级概括中规划“研究框架图”")
        if "年报" not in chapter_four:
            errors.append("第4章案例简介必须在三级概括中规划企业年报数字画像")
        model_text = chapter_three + chapter_four
        model_families = {
            "市场份额": bool(re.search(r"市场份额", model_text)),
            "协同效应": bool(re.search(r"协同效应", model_text)),
            "文化溢价DID": bool(re.search(r"文化溢价|双重差分|\bDID\b", model_text, re.IGNORECASE)),
            "DEA-Tobit": bool(re.search(r"DEA\s*[-‑—]?\s*Tobit|DEA", model_text, re.IGNORECASE)),
        }
        if sum(model_families.values()) < 2:
            errors.append("第3—4章三级概括必须明确至少两类候选实证方法，并在B01只选两种READY模型")
        if not re.search(r"两种[^。\n]{0,50}模型|模型[^。\n]{0,50}两种", model_text):
            errors.append("第3—4章三级概括必须明确“只选择两种模型”的数量约束")

        validate_fixed_number_sets(parsed, errors)

        for number, (name, chunk) in parsed[5].items():
            validate_tertiary_summary(f"{number} {name}", chunk, errors)

        eighth_start = directory.find("### 8. 发展瓶颈")
        ninth_start = directory.find("### 9. 经营优化方案")
        eighth = directory[eighth_start:ninth_start] if eighth_start >= 0 and ninth_start > eighth_start else ""
        bottleneck_count = len(
            re.findall(r"^<!-- BOTTLENECK_ITEM -->\s*$", eighth, re.MULTILINE)
        )
        if not 2 <= bottleneck_count <= 4:
            errors.append(f"发展瓶颈必须标记 2—4 项；当前识别到 {bottleneck_count} 项")

        tenth_start = directory.find("### 10. 结论与启示")
        ninth = directory[ninth_start:tenth_start] if ninth_start >= 0 and tenth_start > ninth_start else ""
        solution_count = len(
            re.findall(r"^<!-- SOLUTION_ITEM -->\s*$", ninth, re.MULTILINE)
        )
        if not 2 <= solution_count <= 4:
            errors.append(f"经营优化方案必须标记 2—4 项；当前识别到 {solution_count} 项")
        if solution_count != bottleneck_count:
            errors.append(
                f"瓶颈与方案数量必须一致；当前瓶颈 {bottleneck_count} 项、方案 {solution_count} 项"
            )

        if 2 <= bottleneck_count <= 4:
            validate_result_items(
                parsed,
                "8",
                bottleneck_count,
                ("问题表现在哪里", "为什么会出现", "会带来什么影响"),
                ("瓶颈识别", "内部挑战", "外部挑战", "地区挑战", "原因树"),
                "发展瓶颈",
                errors,
            )
        if 2 <= solution_count <= 4:
            validate_result_items(
                parsed,
                "9",
                solution_count,
                ("具体怎么做", "谁来做、何时做、需要什么", "怎么判断有效、何时调整"),
                ("方案设计", "行动组合", "实施路径", "效果测量", "风险与回滚"),
                "经营优化方案",
                errors,
            )

    if register:
        validate_register(register, errors)
    if "`UNSUPPORTED_CLAIMS = 0`" not in text:
        errors.append("缺少不支持主张声明：`UNSUPPORTED_CLAIMS = 0`")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验流通业经营模拟赛道分析报告框架确认单的固定三级结构、经营维度、瓶颈/方案数量、六项附录和证据状态。"
    )
    parser.add_argument("framework", type=Path, help="待校验的 Markdown 确认单")
    args = parser.parse_args()
    errors = validate(args.framework)
    if errors:
        print("FAIL: 分析报告框架确认单未通过校验")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 精简11章三级框架、引言研究框架图、案例年报双模型、五个核心经营维度、2—4项瓶颈/方案、六项附录与证据状态均通过校验")
    return 0


if __name__ == "__main__":
    sys.exit(main())
