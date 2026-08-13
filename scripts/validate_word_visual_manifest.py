#!/usr/bin/env python3
"""Validate the rendered-page visual coverage manifest for a CUBEC report."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ALLOWED_KINDS = {"image", "table"}
ALLOWED_SCOPES = {"B01", "B02", "B03", "FINAL"}
ALLOWED_PAGE_ROLES = {"cover", "directory", "narrative", "appendix", "references"}
FORBIDDEN_SUBTYPES = {"decorative", "logo-only", "watermark", "prose-wrapper"}
PAGE_QA_KEYS = (
    "visual_present",
    "relevant_to_adjacent_claim",
    "source_visible_or_mapped",
    "readable_at_100_percent",
    "not_decorative_or_prose_table",
    "render_reviewed",
)
DOCUMENT_CHECK_KEYS = (
    "all_pages_rendered",
    "all_pages_have_qualified_visual",
    "captions_and_sources_checked",
    "figure_captions_below_centered",
    "table_captions_above_centered",
    "caption_fonts_and_seq_fields_checked",
    "figure_text_readability_checked",
    "all_figures_have_lead_in_body_text",
    "no_captions_embedded_in_images",
    "figure_internal_text_meets_large_type_standard",
    "table_cells_centered_without_first_line_indent",
    "toc_includes_heading_levels_1_to_3",
    "only_chapter_breaks_create_new_pages",
    "body_line_spacing_checked",
    "references_are_numbered_paragraphs_not_tables",
    "docx_format_validation_passed",
    "header_footer_reviewed",
    "anonymous_content_and_metadata",
    "docx_revalidated_after_last_reflow",
    "reader_facing_text_validation_passed",
    "consulting_report_voice_reviewed",
    "internal_artifacts_removed",
    "visual_reframing_reviewed",
    "report_visual_map_validation_passed",
)


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_text(item) for item in value)
    )


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["根对象必须是JSON对象"]

    if data.get("template_mode") is not False:
        errors.append("template_mode 必须改为 false，模板示例不能作为实际验收清单")

    for key in ("schema_version", "document_id", "source_report_version", "docx_file", "visual_map_file", "rendered_pdf"):
        if not nonempty_text(data.get(key)):
            errors.append(f"{key} 必须是非空字符串")

    if data.get("delivery_scope") not in ALLOWED_SCOPES:
        errors.append("delivery_scope 必须为 B01、B02、B03 或 FINAL")
    elif data.get("delivery_scope") in {"B02", "B03"} and str(data.get("visual_map_file", "")).strip() in {"", "不适用"}:
        errors.append("B02/B03 的 visual_map_file 必须指向已通过生产校验的图表地图")

    minimum_ratio = data.get("minimum_narrative_image_page_ratio")
    if not isinstance(minimum_ratio, (int, float)) or isinstance(minimum_ratio, bool) or not 0.6 <= minimum_ratio <= 1:
        errors.append("minimum_narrative_image_page_ratio 必须为0.6到1之间的数字")
        minimum_ratio = 0.6

    layout = data.get("layout")
    if not isinstance(layout, dict):
        errors.append("layout 必须是对象")
    else:
        if layout.get("page_size") != "A4":
            errors.append("layout.page_size 必须为 A4")
        if layout.get("orientation") != "portrait":
            errors.append("layout.orientation 必须为 portrait")
        if not nonempty_text(layout.get("design_profile")):
            errors.append("layout.design_profile 必须是非空字符串")
        margins = layout.get("margins_cm")
        if not isinstance(margins, dict):
            errors.append("layout.margins_cm 必须是对象")
        else:
            expected_margins = {"top": 2.54, "bottom": 2.54, "left": 3.17, "right": 3.17}
            for side, expected in expected_margins.items():
                if margins.get(side) != expected:
                    errors.append(f"layout.margins_cm.{side} 必须为 {expected}")

    typography = data.get("typography")
    if not isinstance(typography, dict):
        errors.append("typography 必须是对象")
    else:
        expected_typography = {
            "body_chinese_font": "宋体",
            "body_latin_and_digits_font": "Times New Roman",
            "body_size_pt": 12,
            "body_alignment": "justified",
            "first_line_indent_chars": 2,
            "line_spacing_multiple": 1.25,
            "heading_1": "14pt 黑体加粗",
            "heading_2": "12pt 宋体加粗",
            "heading_3": "12pt 宋体加粗",
        }
        for key, expected in expected_typography.items():
            if typography.get(key) != expected:
                errors.append(f"typography.{key} 必须为 {expected}")

    captions = data.get("captions")
    if not isinstance(captions, dict):
        errors.append("captions 必须是对象")
    else:
        expected_captions = {
            "figure_position": "below",
            "table_position": "above",
            "alignment": "center",
            "chinese_font": "黑体",
            "latin_and_digits_font": "Times New Roman",
            "size_pt": 9,
            "numbering": "automatic-word-seq-fields",
        }
        for key, expected in expected_captions.items():
            if captions.get(key) != expected:
                errors.append(f"captions.{key} 必须为 {expected}")

    figure_text_standard = data.get("figure_text_standard")
    expected_figure_text_standard = {
        "minimum_internal_text_size_pt": 14,
        "key_label_text_size_pt": 16,
        "applies_to_all_visible_text": True,
        "evaluated_at_final_word_width": True,
        "split_instead_of_shrink": True,
    }
    if not isinstance(figure_text_standard, dict):
        errors.append("figure_text_standard 必须是对象")
    else:
        for key, expected in expected_figure_text_standard.items():
            if figure_text_standard.get(key) != expected:
                errors.append(f"figure_text_standard.{key} 必须为 {expected}")

    table_layout = data.get("table_layout")
    expected_table_layout = {
        "cell_horizontal_alignment": "center",
        "cell_vertical_alignment": "center",
        "cell_first_line_indent_chars": 0,
    }
    if not isinstance(table_layout, dict):
        errors.append("table_layout 必须是对象")
    else:
        for key, expected in expected_table_layout.items():
            if table_layout.get(key) != expected:
                errors.append(f"table_layout.{key} 必须为 {expected}")

    toc = data.get("table_of_contents")
    if not isinstance(toc, dict):
        errors.append("table_of_contents 必须是对象")
    else:
        if toc.get("field_based") is not True:
            errors.append("table_of_contents.field_based 必须为 true")
        if toc.get("heading_levels") != [1, 2, 3]:
            errors.append("table_of_contents.heading_levels 必须为 [1, 2, 3]")

    pagination = data.get("pagination")
    if not isinstance(pagination, dict):
        errors.append("pagination 必须是对象")
    else:
        if pagination.get("chapter_break_method") != "heading-1-page-break-before":
            errors.append("pagination.chapter_break_method 必须为 heading-1-page-break-before")
        if pagination.get("manual_page_breaks_present") is not False:
            errors.append("pagination.manual_page_breaks_present 必须为 false")
        if pagination.get("section_breaks_used_for_pagination") is not False:
            errors.append("pagination.section_breaks_used_for_pagination 必须为 false")

    references = data.get("references")
    if not isinstance(references, dict):
        errors.append("references 必须是对象")
    else:
        if references.get("standard") != "GB/T 7714-2025":
            errors.append("references.standard 必须为 GB/T 7714-2025")
        if references.get("layout") != "numeric-sequence-paragraph-list":
            errors.append("references.layout 必须为 numeric-sequence-paragraph-list")
        if references.get("uses_table_layout") is not False:
            errors.append("references.uses_table_layout 必须为 false")
        if references.get("hanging_indent_chars") != 2:
            errors.append("references.hanging_indent_chars 必须为 2")

    for part_name in ("header", "footer"):
        part = data.get(part_name)
        if not isinstance(part, dict):
            errors.append(f"{part_name} 必须是对象")
            continue
        if part.get("contains_school_or_personal_info") is not False:
            errors.append(f"{part_name}.contains_school_or_personal_info 必须为 false")

    page_count = data.get("page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        errors.append("page_count 必须是大于0的整数")
        page_count = 0

    pages = data.get("pages")
    if not isinstance(pages, list):
        errors.append("pages 必须是数组")
        pages = []
    if page_count and len(pages) != page_count:
        errors.append(f"pages 数量 {len(pages)} 与 page_count {page_count} 不一致")

    actual_numbers: list[int] = []
    visual_ids: set[str] = set()
    narrative_image_flags: list[tuple[int, bool]] = []
    for index, page in enumerate(pages, start=1):
        where = f"pages[{index - 1}]"
        if not isinstance(page, dict):
            errors.append(f"{where} 必须是对象")
            continue

        number = page.get("page")
        if not isinstance(number, int) or isinstance(number, bool):
            errors.append(f"{where}.page 必须是整数")
        else:
            actual_numbers.append(number)
        for key in ("rendered_png", "chapter"):
            if not nonempty_text(page.get(key)):
                errors.append(f"{where}.{key} 必须是非空字符串")

        page_role = page.get("page_role")
        if page_role not in ALLOWED_PAGE_ROLES:
            errors.append(f"{where}.page_role 必须为 {sorted(ALLOWED_PAGE_ROLES)} 之一")

        visuals = page.get("visuals")
        if not isinstance(visuals, list) or not visuals:
            errors.append(f"{where}.visuals 至少包含一张合格图片或一张合格表格")
            visuals = []
        for visual_index, visual in enumerate(visuals, start=1):
            vwhere = f"{where}.visuals[{visual_index - 1}]"
            if not isinstance(visual, dict):
                errors.append(f"{vwhere} 必须是对象")
                continue
            visual_id = visual.get("id")
            if not nonempty_text(visual_id):
                errors.append(f"{vwhere}.id 必须是非空字符串")
            elif visual_id in visual_ids:
                errors.append(f"{vwhere}.id 与其他视觉重复：{visual_id}")
            else:
                visual_ids.add(visual_id)

            kind = visual.get("kind")
            if kind not in ALLOWED_KINDS:
                errors.append(f"{vwhere}.kind 只能是 image 或 table")
            subtype = visual.get("subtype")
            if not nonempty_text(subtype):
                errors.append(f"{vwhere}.subtype 必须是非空字符串")
            elif subtype.strip().lower() in FORBIDDEN_SUBTYPES:
                errors.append(f"{vwhere}.subtype 属于禁止的装饰/凑数类型：{subtype}")

            for key in ("title", "purpose"):
                if not nonempty_text(visual.get(key)):
                    errors.append(f"{vwhere}.{key} 必须是非空字符串")
            for key in ("claim_ids", "source_ids"):
                if not nonempty_text_list(visual.get(key)):
                    errors.append(f"{vwhere}.{key} 必须是至少含一个非空字符串的数组")
            if kind == "image":
                if visual.get("lead_in_body_paragraph_present") is not True:
                    errors.append(f"{vwhere}.lead_in_body_paragraph_present 必须为 true")
                if visual.get("contains_embedded_caption") is not False:
                    errors.append(f"{vwhere}.contains_embedded_caption 必须为 false")
                contains_text = visual.get("contains_text")
                if not isinstance(contains_text, bool):
                    errors.append(f"{vwhere}.contains_text 必须为布尔值")
                elif contains_text:
                    internal_size = visual.get("internal_text_size_pt")
                    key_size = visual.get("key_label_text_size_pt")
                    if (
                        not isinstance(internal_size, (int, float))
                        or isinstance(internal_size, bool)
                        or internal_size < 14
                    ):
                        errors.append(f"{vwhere}.internal_text_size_pt 在最终Word宽度下不得小于 14")
                    if (
                        not isinstance(key_size, (int, float))
                        or isinstance(key_size, bool)
                        or key_size < 16
                    ):
                        errors.append(f"{vwhere}.key_label_text_size_pt 在最终Word宽度下不得小于 16")
                else:
                    if visual.get("internal_text_size_pt") is not None:
                        errors.append(f"{vwhere}.internal_text_size_pt 在无文字图片中必须为 null")
                    if visual.get("key_label_text_size_pt") is not None:
                        errors.append(f"{vwhere}.key_label_text_size_pt 在无文字图片中必须为 null")

        if page_role == "narrative" and isinstance(number, int):
            narrative_image_flags.append(
                (number, any(isinstance(item, dict) and item.get("kind") == "image" for item in visuals))
            )

        qa = page.get("qa")
        if not isinstance(qa, dict):
            errors.append(f"{where}.qa 必须是对象")
        else:
            for key in PAGE_QA_KEYS:
                if qa.get(key) is not True:
                    errors.append(f"{where}.qa.{key} 必须为 true")

    if page_count and actual_numbers != list(range(1, page_count + 1)):
        errors.append(
            f"页面编号必须按1到{page_count}连续排列，当前为 {actual_numbers}"
        )

    if not narrative_image_flags:
        errors.append("pages 至少要包含一页 page_role=narrative 的报告正文")
    else:
        image_pages = sum(1 for _, has_image in narrative_image_flags if has_image)
        required_image_pages = math.ceil(len(narrative_image_flags) * float(minimum_ratio))
        if image_pages < required_image_pages:
            errors.append(
                f"叙述性页面含分析性图片的页面数为 {image_pages}/{len(narrative_image_flags)}，"
                f"至少需要 {required_image_pages} 页"
            )
        for (first_page, first_has_image), (second_page, second_has_image) in zip(
            narrative_image_flags, narrative_image_flags[1:]
        ):
            if second_page == first_page + 1 and not first_has_image and not second_has_image:
                errors.append(
                    f"第{first_page}页和第{second_page}页连续两张叙述性页面均无分析性图片"
                )

    checks = data.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks 必须是对象")
    else:
        for key in DOCUMENT_CHECK_KEYS:
            if checks.get(key) is not True:
                errors.append(f"checks.{key} 必须为 true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验Word最终渲染页是否逐页包含合格图片或表格"
    )
    parser.add_argument("manifest", type=Path, help="word visual manifest JSON")
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL\n- 文件不存在：{args.manifest}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"FAIL\n- JSON格式错误：{exc}")
        return 2

    errors = validate(data)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "PASS: 已记录连续渲染页、每页至少一张有主张/来源映射的合格图片或表格，"
        "并完成图片前置正文、图内无题注、图内最小14pt/关键文字16pt、表格居中、三级目录、章节分页、"
        "1.25倍行距、读者正文、页眉页脚、匿名与重排后复核。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
