#!/usr/bin/env python3
"""Preflight a CUBEC circulation project without judging research truth."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Check:
    level: str
    code: str
    message: str


REQUIRED_SECTIONS = {
    "目录": ("目录",),
    "概要": ("概要", "摘要"),
    "引言": ("引言",),
    "案例简介": ("案例简介", "企业简介"),
    "企业内部分析": ("企业内部分析",),
    "企业外部分析": ("企业外部分析",),
    "企业经营模式": ("企业经营模式",),
    "发展瓶颈": ("发展瓶颈", "瓶颈诊断"),
    "经营优化方案": ("经营优化方案", "解决方案"),
    "结论与启示": ("结论与启示", "结论"),
    "附录及参考资料": ("附录", "参考资料", "参考文献"),
}
REQUIRED_APPENDIX_ITEMS = {
    "企业重要数据概览": ("企业重要数据概览",),
    "调查问卷": ("调查问卷",),
    "访谈纲要（含知情说明与编码）": ("访谈纲要（含知情说明与编码）",),
    "参考文献": ("参考文献",),
    "观察/竞品与现场记录": ("观察/竞品与现场记录",),
    "补充图表与地区对标": ("补充图表与地区对标",),
}
CORE_DIMENSIONS = {
    "战略": ("战略",),
    "商业模式": ("商业模式", "经营模式"),
    "运营管理": ("运营", "供应链", "采购", "仓储", "配送", "库存"),
    "市场竞争": ("竞争", "市场", "消费者"),
    "财务状况": ("财务", "利润", "成本", "现金流", "周转", "单位经济"),
}
PLACEHOLDER_RE = re.compile(
    r"\[(?:待调研|待核验|团队判断|待填写|章节|负责人|企业名称|作品名称|团队名称)[^\]]*\]"
)
CONTACT_RE = re.compile(r"(?:1[3-9]\d{9}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})")
SOURCE_MARKERS = re.compile(r"(?:来源|资料来源|参考文献|参考资料|https?://|doi[:：]|访问日期)", re.I)
NUMBER_RE = re.compile(
    r"(?<![A-Za-z])\d+(?:\.\d+)?\s*(?:%|亿元|万元|元|家|个|吨|小时|分钟|天|年|人|单|公里|平方米|㎡)"
)
VALID_DUPLICATE_STATUSES = {"PROVISIONAL", "REVIEW", "BLOCK", "CLEAR_IN_FILE", "CONFIRMED_CLEAR"}


def read_text(path: Path) -> str:
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Only .md and .txt reports are supported; inspect PDF/DOCX with the matching skill first.")


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def validate(report: Path, meta: dict) -> list[Check]:
    text = read_text(report)
    checks: list[Check] = []

    for name, terms in REQUIRED_SECTIONS.items():
        if not contains_any(text, terms):
            checks.append(Check("error", "missing_section", f"缺少官方最低模块：{name}"))
    for name, terms in REQUIRED_APPENDIX_ITEMS.items():
        if not all(term in text for term in terms):
            checks.append(Check("error", "missing_appendix_item", f"缺少固定附录内容：{name}"))
    for name, terms in CORE_DIMENSIONS.items():
        if not contains_any(text, terms):
            checks.append(Check("warning", "missing_dimension", f"未识别到核心经营维度：{name}"))

    compact = re.sub(r"\s+", "", text)
    if len(compact) < 3000:
        checks.append(Check("error", "short_report", f"可识别非空字符约{len(compact)}，低于3000字基线"))
    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        checks.append(Check("error", "placeholders", f"仍有{len(placeholders)}个待处理占位符"))
    contacts = CONTACT_RE.findall(text)
    if contacts:
        checks.append(Check("error", "contact_leak", f"检测到{len(contacts)}处手机号或邮箱"))

    school = str(meta.get("school_name", "")).strip()
    if school and not school.startswith("[") and school in text:
        checks.append(Check("error", "school_leak", "作品内部检测到院校名称"))
    names = [str(item).strip() for item in meta.get("participant_names", []) if str(item).strip()]
    leaked = [name for name in names if name in text]
    if leaked:
        checks.append(Check("error", "name_leak", f"作品内部检测到参赛人员姓名：{', '.join(leaked)}"))

    province = str(meta.get("province", "")).strip()
    if province and not province.startswith("[") and province not in text:
        checks.append(Check("error", "missing_region", f"正文未出现目标地区“{province}”"))
    if not SOURCE_MARKERS.search(text):
        checks.append(Check("warning", "no_sources", "未识别到来源标记或参考资料"))
    if len(NUMBER_RE.findall(text)) >= 8 and len(SOURCE_MARKERS.findall(text)) < 3:
        checks.append(Check("warning", "numeric_traceability", "数字较多但来源标记偏少"))

    pages = meta.get("ppt_pages")
    if pages is None:
        checks.append(Check("warning", "ppt_unknown", "未提供PPT页数，需人工确认不少于20页"))
    else:
        try:
            page_count = int(pages)
        except (TypeError, ValueError):
            checks.append(Check("error", "ppt_invalid", "ppt_pages必须是整数"))
        else:
            if page_count < 20:
                checks.append(Check("error", "ppt_short", f"PPT仅{page_count}页，低于官方20页下限"))
            elif page_count != 20:
                checks.append(Check("warning", "ppt_working_standard", f"PPT为{page_count}页；本skill初版标准为恰好20页"))

    duplicate_status = meta.get("duplicate_enterprise_status")
    if duplicate_status not in VALID_DUPLICATE_STATUSES:
        checks.append(Check("error", "duplicate_status_invalid", "查重状态字段无效"))
    elif duplicate_status != "CONFIRMED_CLEAR":
        level = "error" if duplicate_status == "BLOCK" else "warning"
        checks.append(Check(level, "duplicate_unverified", f"同校企业查重尚未达到CONFIRMED_CLEAR：{duplicate_status}"))
    if meta.get("enterprise_present_in_province") is not True:
        checks.append(Check("error", "regional_presence_unverified", "未确认企业在院校所在省有实际布局"))
    if meta.get("team_human_verification_complete") is not True:
        checks.append(Check("warning", "human_verification_incomplete", "团队尚未确认事实、引用和实质性人工改写"))

    if not checks:
        checks.append(Check("info", "preflight_clear", "确定性预检未发现问题；仍需人工复核事实、原创性和评分质量"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown or text report")
    parser.add_argument("--meta", type=Path, help="JSON metadata file")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    meta = {}
    try:
        if args.meta:
            meta = json.loads(args.meta.read_text(encoding="utf-8"))
        checks = validate(args.report, meta)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(check) for check in checks], ensure_ascii=False, indent=2))
    else:
        for check in checks:
            print(f"[{check.level.upper()}] {check.code}: {check.message}")
    return 1 if any(check.level == "error" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
