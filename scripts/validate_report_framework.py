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
    "2.1": "案例问题与研究设计",
    "2.2": "核心发现与行动结论",
    "3.1": "研究背景与选题价值",
    "3.2": "研究问题与分析框架",
    "3.3": "数据、方法与研究边界",
    "4.1": "企业基本画像",
    "4.2": "业务与地区布局",
    "4.3": "成功机制与阶段特征",
    "5.1": "企业战略",
    "5.2": "资源与组织能力",
    "5.3": "产品与客户运营",
    "5.4": "运营管理",
    "5.5": "财务状况",
    "6.1": "宏观与地区环境",
    "6.2": "行业与市场演进",
    "6.3": "市场竞争",
    "6.4": "外部机会与约束",
    "7.1": "商业模式",
    "7.2": "流通价值链与经营机制",
    "7.3": "地区适配与扩张机制",
    "7.4": "五维联动与阶段错配",
    "8.1": "瓶颈识别与优先级",
    "9.1": "方案设计原则与映射",
    "9.2": "行动组合",
    "9.3": "实施路径与组织保障",
    "9.4": "效果测量、风险与回滚",
    "10.1": "研究结论",
    "10.2": "企业与行业启示",
    "10.3": "适用边界与研究局限",
    "11.1": "参考资料",
    "11.2": "调研工具与样本说明",
    "11.3": "数据处理与证据台账",
    "11.4": "补充材料",
}

CORE_DIMENSIONS = {
    "5.1": "企业战略",
    "5.4": "运营管理",
    "5.5": "财务状况",
    "6.3": "市场竞争",
    "7.1": "商业模式",
}

REQUIRED_TERTIARY = {
    "1.1.1": "章节层级与页码索引",
    "2.1.1": "研究对象、地区与核心问题",
    "2.1.2": "数据、方法与研究边界",
    "2.2.1": "核心机制与发展瓶颈",
    "2.2.2": "经营方案、验证与适用边界",
    "3.1.1": "行业与地区背景",
    "3.1.2": "选题缘由与案例典型性",
    "3.1.3": "研究价值与决策对象",
    "3.2.1": "研究问题与目标",
    "3.2.2": "研究内容与范围",
    "3.2.3": "技术路线与核心因果链",
    "3.3.1": "数据来源与样本设计",
    "3.3.2": "分析方法与工具适配",
    "3.3.3": "研究创新、伦理与局限",
    "4.1.1": "企业主体与业态定位",
    "4.1.2": "发展历程与关键节点",
    "4.1.3": "业务结构与组织范围",
    "4.2.1": "核心业务、产品与服务",
    "4.2.2": "渠道、门店/网点与仓配布局",
    "4.2.3": "目标地区经营基础与阶段",
    "4.3.1": "既有优势与成功基础",
    "4.3.2": "关键事件与阶段变化",
    "4.3.3": "案例典型性与研究接口",
    "5.1.1": "战略定位与经营目标",
    "5.1.2": "增长路径与地区战略",
    "5.1.3": "资源配置与战略执行一致性",
    "5.2.1": "关键资源与核心能力",
    "5.2.2": "组织结构、协同与激励",
    "5.2.3": "数字化、系统与数据能力",
    "5.3.1": "产品/品类与服务组合",
    "5.3.2": "渠道、营销与用户运营",
    "5.3.3": "顾客体验与服务闭环",
    "5.4.1": "采购、供应链与伙伴协同",
    "5.4.2": "仓配、门店/网点与履约流程",
    "5.4.3": "库存、效率、质量与风险控制",
    "5.5.1": "收入、利润与成本结构",
    "5.5.2": "现金、周转与资本效率",
    "5.5.3": "单位经济、代理指标与局限",
    "6.1.1": "政策与制度环境",
    "6.1.2": "经济、人口与社会文化环境",
    "6.1.3": "技术、基础设施与地理条件",
    "6.2.1": "行业规模、阶段与趋势",
    "6.2.2": "顾客、场景与渠道变化",
    "6.2.3": "供应生态与流通链变化",
    "6.3.1": "竞争者、替代方案与竞争边界",
    "6.3.2": "同口径竞争对标与企业位置",
    "6.3.3": "竞争压力、机会与经营传导",
    "6.4.1": "外部机会及进入机制",
    "6.4.2": "外部约束及影响机制",
    "6.4.3": "情景变化与关键不确定性",
    "7.1.1": "顾客、场景与价值主张",
    "7.1.2": "渠道、关系与价值交付",
    "7.1.3": "收入成本、伙伴与价值获取",
    "7.2.1": "采购供应与前端需求连接",
    "7.2.2": "商品、信息与资金流协同",
    "7.2.3": "价值创造、价值泄漏与关键杠杆",
    "7.3.1": "全国标准与地方经营接口",
    "7.3.2": "目标地区适配动作与差距",
    "7.3.3": "复制、规模化与边界条件",
    "7.4.1": "战略—商业模式一致性",
    "7.4.2": "运营—竞争—财务传导链",
    "7.4.3": "优势机制向阶段约束转化",
    "8.1.1": "症状、差距与经营影响",
    "8.1.2": "原因树与替代解释",
    "8.1.3": "影响—可控性—紧迫性排序",
    "9.1.1": "根因—行动镜像映射",
    "9.1.2": "目标对象、地区适配与创新点",
    "9.1.3": "方案组合与优先顺序",
    "9.3.1": "0—3 个月试点",
    "9.3.2": "3—12 个月推广",
    "9.3.3": "责任、资源、预算与协同",
    "9.4.1": "过程 KPI、结果 KPI 与数据采集",
    "9.4.2": "情景、敏感性与可行性",
    "9.4.3": "风险触发、停止条件与回滚",
    "10.1.1": "研究问题逐项回答",
    "10.1.2": "优势、错配与瓶颈机制",
    "10.1.3": "方案价值与验证结论",
    "10.2.1": "对案例企业的经营启示",
    "10.2.2": "对目标地区流通业的启示",
    "10.2.3": "对同类企业的可迁移启示",
    "10.3.1": "适用条件与不可复制条件",
    "10.3.2": "数据、样本与方法局限",
    "10.3.3": "后续研究与验证计划",
    "11.1.1": "政策、政府与统计来源",
    "11.1.2": "企业、行业与市场来源",
    "11.1.3": "学术、媒体与网络来源",
    "11.2.1": "访谈提纲、知情说明与编码",
    "11.2.2": "问卷、样本结构与质量控制",
    "11.2.3": "观察、竞品与现场记录",
    "11.3.1": "数据清洗、排除与口径说明",
    "11.3.2": "主张—证据台账与反证",
    "11.3.3": "公式、计算与复现说明",
    "11.4.1": "补充图表与地区对标",
    "11.4.2": "方案假设与敏感性底稿",
    "11.4.3": "匿名、伦理与版本记录",
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

        for number in ("9.2.1", "9.2.2"):
            if number not in parsed[5]:
                errors.append(f"经营优化方案至少缺少行动包：{number}")

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

    if register:
        validate_register(register, errors)
    if "`UNSUPPORTED_CLAIMS = 0`" not in text:
        errors.append("缺少不支持主张声明：`UNSUPPORTED_CLAIMS = 0`")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验流通业经营模拟赛道分析报告框架确认单的固定三级结构、经营维度、瓶颈数量和证据状态。"
    )
    parser.add_argument("framework", type=Path, help="待校验的 Markdown 确认单")
    args = parser.parse_args()
    errors = validate(args.framework)
    if errors:
        print("FAIL: 分析报告框架确认单未通过校验")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 固定 11 章三级框架、五个核心经营维度、2—4 项瓶颈与证据状态均通过校验")
    return 0


if __name__ == "__main__":
    sys.exit(main())
