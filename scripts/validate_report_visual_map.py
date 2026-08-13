#!/usr/bin/env python3
"""Validate B02/B03 report visual coverage, evidence, and style diversity."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ALLOWED_BATCHES = {"B02", "B03"}
ALLOWED_KINDS = {"image", "table"}
ALLOWED_FAMILIES = {
    "table-scorecard",
    "trend",
    "comparison-ranking",
    "composition-distribution",
    "relationship",
    "matrix-heatmap",
    "geography",
    "text-mining",
    "decomposition",
    "process-roadmap",
    "evidence-photo",
}
ALLOWED_FORMS = {
    "data-table",
    "line",
    "heatmap",
    "word-cloud",
    "bar",
    "combo",
    "map",
    "radar",
    "waterfall",
    "pareto",
    "scatter",
    "boxplot",
    "process",
    "roadmap",
    "matrix",
    "photo",
    "other",
}
REQUESTED_FORMS = {"data-table", "line", "heatmap", "word-cloud", "bar", "combo"}
ALLOWED_STYLES = {
    "accent-monochrome",
    "focal-vs-context",
    "sequential-heat",
    "multi-category",
    "signed-delta",
    "solution-roadmap",
    "tinted-table",
    "documentary-photo",
}
ALLOWED_LAYOUTS = {
    "full-width",
    "text-left-visual-right",
    "visual-left-text-right",
    "table-chart-pair",
    "paired-visuals",
    "small-multiples",
    "full-page-map",
    "process-band",
    "appendix-grid",
}
ALLOWED_STATUSES = {"PLANNED", "PRODUCED", "VERIFIED"}
CHECK_KEYS = (
    "all_required_sections_mapped",
    "all_claims_source_bound",
    "data_sufficiency_reviewed",
    "requested_forms_reviewed",
    "style_diversity_reviewed",
    "sample_style_not_copied",
    "final_surface_planned",
)

B02_SECTIONS = {
    f"{chapter}.{second}.{third}"
    for chapter in (5, 6, 7)
    for second in (1, 2, 3)
    for third in (1, 2, 3)
}
B03_FIXED_SECTIONS = {
    "10.1.1", "10.1.2", "10.1.3",
    "10.2.1", "10.2.2", "10.2.3",
    "10.3.1", "10.3.2", "10.3.3",
    "11.1.1",
    "11.2.1", "11.2.2",
    "11.3.1", "11.3.2",
    "11.4.1", "11.4.2",
    "11.5.1", "11.5.2",
    "11.6.1", "11.6.2",
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_text_list(value: Any, minimum: int = 1) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(nonempty_text(item) for item in value)
    )


def validate_required_sections(batch: str, sections: set[str]) -> list[str]:
    errors: list[str] = []
    if batch == "B02":
        missing = B02_SECTIONS - sections
        extra = sections - B02_SECTIONS
        if missing:
            errors.append(f"B02 required_sections 缺少固定三级标题：{sorted(missing)}")
        if extra:
            errors.append(f"B02 required_sections 出现框架外标题：{sorted(extra)}")
        return errors

    missing_fixed = B03_FIXED_SECTIONS - sections
    if missing_fixed:
        errors.append(f"B03 required_sections 缺少第10—11章固定三级标题：{sorted(missing_fixed)}")
    bottlenecks: dict[int, set[int]] = defaultdict(set)
    solutions: dict[int, set[int]] = defaultdict(set)
    for section in sections:
        match = re.fullmatch(r"([89])\.(\d+)\.([123])", section)
        if match:
            target = bottlenecks if match.group(1) == "8" else solutions
            target[int(match.group(2))].add(int(match.group(3)))
        elif not section.startswith(("10.", "11.")):
            errors.append(f"B03 required_sections 含无效三级标题：{section}")
    expected_numbers = list(range(1, len(bottlenecks) + 1))
    if not 2 <= len(bottlenecks) <= 4 or sorted(bottlenecks) != expected_numbers:
        errors.append("B03 必须包含连续编号的2—4项瓶颈（8.1—8.n）")
    if sorted(solutions) != sorted(bottlenecks):
        errors.append("B03 方案项数量与编号必须和瓶颈项一致")
    for label, groups in (("瓶颈", bottlenecks), ("方案", solutions)):
        for number, thirds in groups.items():
            if thirds != {1, 2, 3}:
                errors.append(f"第{number}项{label}必须包含三个固定三级标题")
    return errors


def validate(data: Any, for_production: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["根对象必须是JSON对象"]
    if data.get("template_mode") is not False:
        errors.append("template_mode 必须改为 false")
    if not nonempty_text(data.get("schema_version")):
        errors.append("schema_version 必须是非空字符串")
    batch = data.get("batch_scope")
    if batch not in ALLOWED_BATCHES:
        errors.append("batch_scope 必须为 B02 或 B03")
        batch = "B02"

    system = data.get("report_visual_system")
    if not isinstance(system, dict):
        errors.append("report_visual_system 必须是对象")
    else:
        for key in ("font_family", "primary_accent", "secondary_accent", "background", "table_style", "sample_style_policy"):
            if not nonempty_text(system.get(key)):
                errors.append(f"report_visual_system.{key} 必须是非空字符串")

    required_raw = data.get("required_sections")
    if not nonempty_text_list(required_raw):
        errors.append("required_sections 必须是非空三级标题数组")
        required_sections: set[str] = set()
    else:
        required_sections = set(required_raw)
        if len(required_sections) != len(required_raw):
            errors.append("required_sections 不能重复")
    errors.extend(validate_required_sections(batch, required_sections))

    requested = data.get("requested_forms")
    requested_decisions: dict[str, str] = {}
    if not isinstance(requested, list):
        errors.append("requested_forms 必须是数组")
        requested = []
    for index, item in enumerate(requested):
        where = f"requested_forms[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where} 必须是对象")
            continue
        form = item.get("form")
        if form not in REQUESTED_FORMS:
            errors.append(f"{where}.form 必须属于 {sorted(REQUESTED_FORMS)}")
            continue
        if form in requested_decisions:
            errors.append(f"{where}.form 重复：{form}")
        decision = item.get("decision")
        if decision not in {"USE", "NOT_APPLICABLE"}:
            errors.append(f"{where}.decision 必须为 USE 或 NOT_APPLICABLE")
        requested_decisions[form] = decision
        if not nonempty_text(item.get("reason")):
            errors.append(f"{where}.reason 必须说明数据适配理由")
        if decision == "NOT_APPLICABLE" and not nonempty_text(item.get("fallback")):
            errors.append(f"{where}.fallback 必须给出替代形式")
    if set(requested_decisions) != REQUESTED_FORMS:
        errors.append(f"requested_forms 必须逐项审查：{sorted(REQUESTED_FORMS)}")
    minimum_used = 4 if batch == "B02" else 3
    if sum(value == "USE" for value in requested_decisions.values()) < minimum_used:
        errors.append(f"{batch} 在六种指定形式中至少应有 {minimum_used} 种通过数据门")

    visuals = data.get("visuals")
    if not isinstance(visuals, list) or not visuals:
        errors.append("visuals 必须是非空数组")
        visuals = []
    ids: set[str] = set()
    visuals_by_id: dict[str, dict[str, Any]] = {}
    mapped_sections: set[str] = set()
    families: list[str] = []
    forms: list[str] = []
    styles: set[str] = set()
    layouts: set[str] = set()
    kinds: set[str] = set()
    triples: list[tuple[str, str, str]] = []
    visuals_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for index, item in enumerate(visuals):
        where = f"visuals[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where} 必须是对象")
            continue
        visual_id = item.get("id")
        if not nonempty_text(visual_id):
            errors.append(f"{where}.id 必须是非空字符串")
        elif visual_id in ids:
            errors.append(f"{where}.id 重复：{visual_id}")
        else:
            ids.add(visual_id)
            visuals_by_id[visual_id] = item
        section = item.get("section")
        if section not in required_sections:
            errors.append(f"{where}.section 不在 required_sections：{section}")
        else:
            mapped_sections.add(section)
            match = re.fullmatch(r"([89])\.(\d+)\.[123]", section)
            if match:
                visuals_by_group[f"{match.group(1)}.{match.group(2)}"].append(item)
        for key in ("question", "takeaway", "variant", "data_file", "period", "geography", "unit", "denominator"):
            if not nonempty_text(item.get(key)):
                errors.append(f"{where}.{key} 必须是非空字符串")
        if not nonempty_text_list(item.get("fields"), minimum=2):
            errors.append(f"{where}.fields 至少包含两个字段")
        if not nonempty_text_list(item.get("source_ids")):
            errors.append(f"{where}.source_ids 至少包含一个来源ID")
        kind = item.get("kind")
        family = item.get("family")
        form = item.get("form")
        style = item.get("style_mode")
        layout = item.get("layout_mode")
        status = item.get("status")
        if kind not in ALLOWED_KINDS:
            errors.append(f"{where}.kind 必须为 image 或 table")
        else:
            kinds.add(kind)
        if family not in ALLOWED_FAMILIES:
            errors.append(f"{where}.family 无效")
        else:
            families.append(family)
        if form not in ALLOWED_FORMS:
            errors.append(f"{where}.form 无效")
        else:
            forms.append(form)
        if style not in ALLOWED_STYLES:
            errors.append(f"{where}.style_mode 无效")
        else:
            styles.add(style)
        if layout not in ALLOWED_LAYOUTS:
            errors.append(f"{where}.layout_mode 无效")
        else:
            layouts.add(layout)
        if status not in ALLOWED_STATUSES:
            errors.append(f"{where}.status 无效")
        if for_production and status != "VERIFIED":
            errors.append(f"{where}.status 在生产校验时必须为 VERIFIED")
        if for_production and not nonempty_text(item.get("output_file")):
            errors.append(f"{where}.output_file 在生产校验时必须存在")
        observations = item.get("actual_observations")
        if not isinstance(observations, int) or isinstance(observations, bool) or observations < 1:
            errors.append(f"{where}.actual_observations 必须为正整数")
            observations = 0
        thresholds = {"line": 8, "bar": 4, "heatmap": 9, "word-cloud": 100, "combo": 4}
        if form in thresholds and observations < thresholds[form]:
            errors.append(f"{where}.{form} 观察量不足，至少需要 {thresholds[form]}")
        if form in {"data-table", "combo"} and not nonempty_text_list(item.get("fields"), minimum=3):
            errors.append(f"{where}.{form} 至少需要三个字段")
        if form == "word-cloud" and not nonempty_text(item.get("companion_visual_id")):
            errors.append(f"{where}.word-cloud 必须绑定词频柱状图或主题表")
        if nonempty_text(family) and nonempty_text(item.get("variant")) and nonempty_text(layout):
            triples.append((family, item["variant"], layout))

    missing_mapped = required_sections - mapped_sections
    if missing_mapped:
        errors.append(f"以下三级标题没有主视觉或数值表：{sorted(missing_mapped)}")
    for index, item in enumerate(visuals):
        if isinstance(item, dict) and item.get("form") == "word-cloud":
            companion = item.get("companion_visual_id")
            if companion not in ids:
                errors.append(f"visuals[{index}].companion_visual_id 未找到：{companion}")
            elif visuals_by_id[companion].get("form") not in {"bar", "data-table", "matrix"}:
                errors.append(f"visuals[{index}].companion_visual_id 必须指向词频柱状图或主题表：{companion}")

    used_forms = set(forms)
    for form, decision in requested_decisions.items():
        if decision == "USE" and form not in used_forms:
            errors.append(f"requested_forms 将 {form} 标为 USE，但 visuals 中未使用")
        if decision == "NOT_APPLICABLE" and form in used_forms:
            errors.append(f"requested_forms 将 {form} 标为 NOT_APPLICABLE，但 visuals 中仍使用")

    coverage = data.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage 必须是对象")
        coverage = {}
    min_families = coverage.get("minimum_unique_families")
    min_styles = coverage.get("minimum_unique_style_modes")
    min_layouts = coverage.get("minimum_unique_layout_modes")
    max_share = coverage.get("maximum_family_share")
    if not isinstance(min_families, int) or min_families < 5:
        errors.append("coverage.minimum_unique_families 至少为5")
        min_families = 5
    if not isinstance(min_styles, int) or min_styles < 3:
        errors.append("coverage.minimum_unique_style_modes 至少为3")
        min_styles = 3
    if not isinstance(min_layouts, int) or min_layouts < 3:
        errors.append("coverage.minimum_unique_layout_modes 至少为3")
        min_layouts = 3
    if not isinstance(max_share, (int, float)) or isinstance(max_share, bool) or not 0 < max_share <= 0.4:
        errors.append("coverage.maximum_family_share 必须大于0且不超过0.4")
        max_share = 0.4
    if len(set(families)) < min_families:
        errors.append(f"视觉家族只有 {len(set(families))} 种，至少需要 {min_families} 种")
    if len(styles) < min_styles:
        errors.append(f"风格模式只有 {len(styles)} 种，至少需要 {min_styles} 种")
    if len(layouts) < min_layouts:
        errors.append(f"页面版式只有 {len(layouts)} 种，至少需要 {min_layouts} 种")
    if families:
        top_family, top_count = Counter(families).most_common(1)[0]
        if top_count / len(families) > float(max_share):
            errors.append(f"视觉家族 {top_family} 占比 {top_count / len(families):.1%}，超过上限 {max_share:.0%}")
    if kinds != {"image", "table"}:
        errors.append("B02/B03 必须同时包含数值表和分析图片")
    for first, second in zip(triples, triples[1:]):
        if first == second:
            errors.append(f"连续两张视觉使用完全相同的家族、变体和版式：{first}")
            break
    for key in ("all_required_sections_mapped", "tables_and_charts_both_present"):
        if coverage.get(key) is not True:
            errors.append(f"coverage.{key} 必须为 true")

    if batch == "B02":
        for chapter in ("5", "6", "7"):
            table_count = sum(
                1 for item in visuals
                if isinstance(item, dict) and str(item.get("section", "")).startswith(chapter + ".") and item.get("kind") == "table"
            )
            if table_count < 2:
                errors.append(f"第{chapter}章至少需要两张数值表")
    else:
        mechanism_families = {"process-roadmap", "relationship", "decomposition"}
        evaluation_families = {"trend", "comparison-ranking", "matrix-heatmap", "decomposition", "composition-distribution"}
        bottleneck_numbers = sorted({key.split(".")[1] for key in visuals_by_group if key.startswith("8.")})
        for number in bottleneck_numbers:
            group = visuals_by_group[f"8.{number}"]
            group_families = {item.get("family") for item in group}
            if not any(item.get("kind") == "table" for item in group):
                errors.append(f"瓶颈8.{number}至少需要一张症状/差距数据表")
            if not (group_families & mechanism_families):
                errors.append(f"瓶颈8.{number}至少需要一张根因机制图")
        for number in bottleneck_numbers:
            group = visuals_by_group[f"9.{number}"]
            group_families = {item.get("family") for item in group}
            if not any(item.get("kind") == "table" for item in group):
                errors.append(f"方案9.{number}至少需要一张实施/KPI数据表")
            if "process-roadmap" not in group_families:
                errors.append(f"方案9.{number}至少需要一张流程或路线图")
            if not (group_families & evaluation_families):
                errors.append(f"方案9.{number}至少需要一张评价或风险图")

    checks = data.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks 必须是对象")
    else:
        for key in CHECK_KEYS:
            if checks.get(key) is not True:
                errors.append(f"checks.{key} 必须为 true")
    return errors


def make_self_test_data() -> dict[str, Any]:
    forms_cycle = ["line", "heatmap", "word-cloud", "bar", "combo", "map", "process", "matrix"]
    family_for = {
        "line": "trend", "heatmap": "matrix-heatmap", "word-cloud": "text-mining",
        "bar": "comparison-ranking", "combo": "trend", "map": "geography",
        "process": "process-roadmap", "matrix": "relationship", "data-table": "table-scorecard",
    }
    style_cycle = ["accent-monochrome", "focal-vs-context", "sequential-heat", "multi-category"]
    layout_cycle = ["full-width", "text-left-visual-right", "visual-left-text-right", "table-chart-pair"]
    sections = sorted(B02_SECTIONS, key=lambda s: tuple(map(int, s.split("."))))
    visuals: list[dict[str, Any]] = []
    table_sections = {f"{chapter}.1.1" for chapter in (5, 6, 7)} | {f"{chapter}.1.2" for chapter in (5, 6, 7)}
    word_cloud_id = "V-5.2.1"
    for index, section in enumerate(sections):
        form = "data-table" if section in table_sections else forms_cycle[index % len(forms_cycle)]
        observations = {"line": 8, "heatmap": 9, "word-cloud": 100, "bar": 4, "combo": 4}.get(form, 6)
        fields = ["对象", "指标", "数值"] if form in {"data-table", "combo"} else ["对象", "数值"]
        visuals.append({
            "id": f"V-{section}", "section": section, "question": "分析问题", "takeaway": "数据支持的判断",
            "kind": "table" if form == "data-table" else "image", "family": family_for[form], "form": form,
            "variant": f"{form}-variant-{index % 3}", "style_mode": "tinted-table" if form == "data-table" else style_cycle[index % len(style_cycle)],
            "layout_mode": layout_cycle[index % len(layout_cycle)], "status": "VERIFIED", "data_file": "data.xlsx",
            "fields": fields, "source_ids": ["E001"], "period": "2024", "geography": "目标地区", "unit": "个",
            "denominator": "样本总体", "actual_observations": observations,
            "companion_visual_id": "V-5.1.1" if form == "word-cloud" else "不适用", "output_file": f"{section}.svg",
        })
    requested = [
        {"form": form, "decision": "USE", "reason": "数据满足", "fallback": "替代图"}
        for form in sorted(REQUESTED_FORMS)
    ]
    return {
        "schema_version": "1.0", "template_mode": False, "batch_scope": "B02",
        "report_visual_system": {"font_family": "Noto Sans CJK", "primary_accent": "#123456", "secondary_accent": "#C58A2A", "background": "#FFFFFF", "table_style": "tinted", "sample_style_policy": "不复制样本"},
        "required_sections": sections, "requested_forms": requested, "visuals": visuals,
        "coverage": {"minimum_unique_families": 5, "minimum_unique_style_modes": 3, "minimum_unique_layout_modes": 3, "maximum_family_share": 0.4, "all_required_sections_mapped": True, "tables_and_charts_both_present": True},
        "checks": {key: True for key in CHECK_KEYS},
    }


def make_b03_self_test_data() -> dict[str, Any]:
    sections = sorted(
        B03_FIXED_SECTIONS
        | {f"{chapter}.{second}.{third}" for chapter in (8, 9) for second in (1, 2) for third in (1, 2, 3)},
        key=lambda s: tuple(map(int, s.split("."))),
    )
    styles = ["accent-monochrome", "focal-vs-context", "sequential-heat", "solution-roadmap"]
    layouts = ["full-width", "text-left-visual-right", "visual-left-text-right", "table-chart-pair"]
    forms = ["line", "bar", "combo", "map", "matrix", "heatmap", "word-cloud"]
    family_for = {
        "data-table": "table-scorecard", "line": "trend", "bar": "comparison-ranking",
        "combo": "trend", "map": "geography", "matrix": "relationship",
        "heatmap": "matrix-heatmap", "word-cloud": "text-mining", "process": "process-roadmap",
    }
    forced_forms = {
        "8.1.1": "data-table", "8.1.2": "process", "8.1.3": "bar",
        "8.2.1": "data-table", "8.2.2": "process", "8.2.3": "combo",
        "9.1.1": "process", "9.1.2": "data-table", "9.1.3": "heatmap",
        "9.2.1": "process", "9.2.2": "data-table", "9.2.3": "bar",
    }
    visuals: list[dict[str, Any]] = []
    for index, section in enumerate(sections):
        form = forced_forms.get(section, forms[index % len(forms)])
        observation_minimum = {"line": 8, "bar": 4, "combo": 4, "heatmap": 9, "word-cloud": 100}.get(form, 6)
        fields = ["对象", "指标", "数值"] if form in {"data-table", "combo"} else ["对象", "数值"]
        visuals.append({
            "id": f"V-{section}", "section": section, "question": "分析问题", "takeaway": "数据支持的判断",
            "kind": "table" if form == "data-table" else "image", "family": family_for[form], "form": form,
            "variant": f"{form}-variant-{index % 3}", "style_mode": "tinted-table" if form == "data-table" else styles[index % len(styles)],
            "layout_mode": layouts[index % len(layouts)], "status": "VERIFIED", "data_file": "data.xlsx",
            "fields": fields, "source_ids": ["E001", "E002"], "period": "2024", "geography": "目标地区",
            "unit": "个", "denominator": "样本总体", "actual_observations": observation_minimum,
            "companion_visual_id": "V-8.1.1" if form == "word-cloud" else "不适用", "output_file": f"{section}.svg",
        })
    requested = [
        {"form": form, "decision": "USE", "reason": "数据满足", "fallback": "替代图"}
        for form in sorted(REQUESTED_FORMS)
    ]
    return {
        "schema_version": "1.0", "template_mode": False, "batch_scope": "B03",
        "report_visual_system": {"font_family": "Noto Sans CJK", "primary_accent": "#123456", "secondary_accent": "#C58A2A", "background": "#FFFFFF", "table_style": "tinted", "sample_style_policy": "不复制样本"},
        "required_sections": sections, "requested_forms": requested, "visuals": visuals,
        "coverage": {"minimum_unique_families": 5, "minimum_unique_style_modes": 3, "minimum_unique_layout_modes": 3, "maximum_family_share": 0.4, "all_required_sections_mapped": True, "tables_and_charts_both_present": True},
        "checks": {key: True for key in CHECK_KEYS},
    }


def self_test() -> int:
    for label, data in (("B02", make_self_test_data()), ("B03", make_b03_self_test_data())):
        errors = validate(data, for_production=True)
        if errors:
            print(f"FAIL: valid {label} visual map rejected")
            for error in errors:
                print(f"- {error}")
            return 1
    data = make_self_test_data()
    data["visuals"] = data["visuals"][:-1]
    errors = validate(data, for_production=True)
    if not any("没有主视觉" in error for error in errors):
        print("FAIL: missing section was not detected")
        return 1
    data = make_self_test_data()
    word_cloud = next(item for item in data["visuals"] if item["form"] == "word-cloud")
    word_cloud["actual_observations"] = 80
    errors = validate(data, for_production=True)
    if not any("word-cloud 观察量不足" in error for error in errors):
        print("FAIL: 80 texts incorrectly passed the word-cloud data gate")
        return 1
    print("PASS: report visual map validator self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="校验B02/B03图表地图、数据门与视觉多样性")
    parser.add_argument("visual_map", nargs="?", type=Path)
    parser.add_argument("--for-production", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.visual_map is None:
        parser.error("visual_map is required unless --self-test is used")
    try:
        data = json.loads(args.visual_map.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL\n- 文件不存在：{args.visual_map}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"FAIL\n- JSON格式错误：{exc}")
        return 2
    errors = validate(data, for_production=args.for_production)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 三级小节视觉覆盖、指定图形审查、数据门、来源和多样风格均通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
