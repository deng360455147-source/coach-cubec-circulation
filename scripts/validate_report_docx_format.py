#!/usr/bin/env python3
"""Validate the deterministic Word layout and caption rules of a CUBEC report."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
V = "urn:schemas-microsoft-com:vml"
NS = {"w": W, "wp": WP, "v": V}
WVAL = f"{{{W}}}val"


def qn(local: str) -> str:
    return f"{{{W}}}{local}"


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError as exc:
        raise ValueError(f"DOCX缺少必要部件：{name}") from exc
    except ET.ParseError as exc:
        raise ValueError(f"{name} XML无法解析：{exc}") from exc


def attr_int(node: ET.Element | None, name: str = WVAL) -> int | None:
    if node is None:
        return None
    value = node.get(name)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def field_instruction(paragraph: ET.Element) -> str:
    return " ".join(node.text or "" for node in paragraph.findall(".//w:instrText", NS))


def direct_child(parent: ET.Element | None, local: str) -> ET.Element | None:
    return None if parent is None else parent.find(f"w:{local}", NS)


def style_index(styles_root: ET.Element) -> tuple[dict[str, ET.Element], dict[str, ET.Element], ET.Element | None]:
    by_id: dict[str, ET.Element] = {}
    by_name: dict[str, ET.Element] = {}
    default_style: ET.Element | None = None
    for style in styles_root.findall("w:style", NS):
        if style.get(qn("type")) != "paragraph":
            continue
        style_id = style.get(qn("styleId"), "")
        name_node = style.find("w:name", NS)
        name = (name_node.get(WVAL, "") if name_node is not None else "").lower()
        if style_id:
            by_id[style_id.lower()] = style
        if name:
            by_name[name] = style
        if style.get(qn("default")) in {"1", "true", "on"}:
            default_style = style
    return by_id, by_name, default_style


def locate_style(
    by_id: dict[str, ET.Element],
    by_name: dict[str, ET.Element],
    default_style: ET.Element | None,
    aliases: Iterable[str],
    allow_default: bool = False,
) -> ET.Element | None:
    for alias in aliases:
        key = alias.lower()
        if key in by_id:
            return by_id[key]
        if key in by_name:
            return by_name[key]
    return default_style if allow_default else None


def style_id(style: ET.Element | None) -> str:
    return "" if style is None else style.get(qn("styleId"), "")


def check_style_font(
    errors: list[str],
    style: ET.Element | None,
    label: str,
    east_asia: str,
    latin: str,
    size_half_points: int,
    bold: bool | None,
) -> None:
    if style is None:
        errors.append(f"缺少{label}段落样式")
        return
    rpr = style.find("w:rPr", NS)
    fonts = direct_child(rpr, "rFonts")
    if fonts is None or fonts.get(qn("eastAsia")) != east_asia:
        errors.append(f"{label}中文字体必须显式设为{east_asia}")
    if fonts is None or fonts.get(qn("ascii")) != latin or fonts.get(qn("hAnsi")) != latin:
        errors.append(f"{label}英文与数字字体必须显式设为{latin}")
    size = attr_int(direct_child(rpr, "sz"))
    if size != size_half_points:
        errors.append(f"{label}字号必须为{size_half_points / 2:g}pt，当前为{size / 2 if size is not None else '未设置'}")
    bold_node = direct_child(rpr, "b")
    bold_enabled = bold_node is not None and bold_node.get(WVAL, "1") not in {"0", "false", "off"}
    if bold is True and not bold_enabled:
        errors.append(f"{label}必须加粗")
    if bold is False and bold_enabled:
        errors.append(f"{label}不应默认加粗")


def check_spacing(
    errors: list[str], style: ET.Element | None, label: str, before: int, after: int
) -> None:
    if style is None:
        return
    ppr = style.find("w:pPr", NS)
    spacing = direct_child(ppr, "spacing")
    actual_before = attr_int(spacing, qn("before"))
    actual_after = attr_int(spacing, qn("after"))
    if actual_before != before or actual_after != after:
        errors.append(
            f"{label}段前/段后必须为{before / 20:g}/{after / 20:g}pt，"
            f"当前为{actual_before / 20 if actual_before is not None else '未设置'}/"
            f"{actual_after / 20 if actual_after is not None else '未设置'}pt"
        )


def paragraph_style_id(paragraph: ET.Element) -> str:
    pstyle = paragraph.find("w:pPr/w:pStyle", NS)
    return "" if pstyle is None else pstyle.get(WVAL, "")


def has_drawing(paragraph: ET.Element) -> bool:
    return paragraph.find(".//w:drawing", NS) is not None or paragraph.find(".//w:pict", NS) is not None


def nonblank_block(block: ET.Element) -> bool:
    if block.tag == qn("tbl"):
        return True
    if block.tag == qn("p"):
        return bool(paragraph_text(block) or has_drawing(block))
    return False


def previous_nonblank(blocks: list[ET.Element], index: int) -> ET.Element | None:
    for block in reversed(blocks[:index]):
        if nonblank_block(block):
            return block
    return None


def next_nonblank(blocks: list[ET.Element], index: int) -> ET.Element | None:
    for block in blocks[index + 1 :]:
        if nonblank_block(block):
            return block
    return None


def validate_docx(path: Path, strict_caption_coverage: bool, final_report: bool) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        document = read_xml(archive, "word/document.xml")
        styles = read_xml(archive, "word/styles.xml")
        settings = read_xml(archive, "word/settings.xml")

    by_id, by_name, default_style = style_index(styles)
    normal = locate_style(by_id, by_name, default_style, ("Normal", "正文"), allow_default=True)
    heading1 = locate_style(by_id, by_name, default_style, ("Heading1", "heading 1", "标题 1", "标题1"))
    heading2 = locate_style(by_id, by_name, default_style, ("Heading2", "heading 2", "标题 2", "标题2"))
    heading3 = locate_style(by_id, by_name, default_style, ("Heading3", "heading 3", "标题 3", "标题3"))
    caption = locate_style(by_id, by_name, default_style, ("Caption", "caption", "题注"))

    check_style_font(errors, normal, "正文", "宋体", "Times New Roman", 24, False)
    check_style_font(errors, heading1, "一级标题", "黑体", "Times New Roman", 28, True)
    check_style_font(errors, heading2, "二级标题", "宋体", "Times New Roman", 24, True)
    check_style_font(errors, heading3, "三级标题", "宋体", "Times New Roman", 24, True)
    check_style_font(errors, caption, "题注", "黑体", "Times New Roman", 21, False)
    check_spacing(errors, heading1, "一级标题", 120, 120)
    check_spacing(errors, heading2, "二级标题", 120, 0)
    check_spacing(errors, heading3, "三级标题", 60, 0)

    if normal is not None:
        ppr = normal.find("w:pPr", NS)
        jc = direct_child(ppr, "jc")
        ind = direct_child(ppr, "ind")
        spacing = direct_child(ppr, "spacing")
        if jc is None or jc.get(WVAL) != "both":
            errors.append("正文必须两端对齐")
        if ind is None or attr_int(ind, qn("firstLineChars")) != 200:
            errors.append("正文首行缩进必须为2字符")
        if spacing is None or attr_int(spacing, qn("line")) != 360 or spacing.get(qn("lineRule")) != "auto":
            errors.append("正文必须显式设置1.5倍行距")

    if caption is not None:
        ppr = caption.find("w:pPr", NS)
        jc = direct_child(ppr, "jc")
        if jc is None or jc.get(WVAL) != "center":
            errors.append("题注样式必须居中")

    body = document.find("w:body", NS)
    if body is None:
        return errors + ["document.xml缺少正文body"]
    sections = document.findall(".//w:sectPr", NS)
    if not sections:
        errors.append("未找到页面节属性")
    for section_number, sect in enumerate(sections, start=1):
        size = sect.find("w:pgSz", NS)
        margins = sect.find("w:pgMar", NS)
        width = attr_int(size, qn("w"))
        height = attr_int(size, qn("h"))
        if width is None or height is None or abs(width - 11906) > 15 or abs(height - 16838) > 15:
            errors.append(f"第{section_number}节页面必须为A4竖版，当前尺寸为{width}×{height} twips")
        expected_margins = {"top": 1440, "bottom": 1440, "left": 1797, "right": 1797}
        for side, expected in expected_margins.items():
            actual = attr_int(margins, qn(side))
            if actual is None or abs(actual - expected) > 15:
                errors.append(f"第{section_number}节{side}页边距必须为预设值{expected} twips，当前为{actual}")

    update_fields = settings.find("w:updateFields", NS)
    if update_fields is None or update_fields.get(WVAL, "1") not in {"1", "true", "on"}:
        errors.append("settings.xml必须启用打开文档时更新域")

    blocks = list(body)
    caption_style_id = style_id(caption).lower()
    caption_count = 0
    for index, block in enumerate(blocks):
        if block.tag != qn("p"):
            continue
        text = paragraph_text(block)
        if not re.match(r"^[图表]\s*\d", text):
            continue
        caption_count += 1
        if paragraph_style_id(block).lower() != caption_style_id:
            errors.append(f"题注“{text[:30]}”未使用统一Caption/题注样式")
        instruction = field_instruction(block)
        if not re.search(r"\bSEQ\b", instruction, re.IGNORECASE):
            errors.append(f"题注“{text[:30]}”没有真实SEQ自动编号域")
        if text.startswith("图"):
            previous = previous_nonblank(blocks, index)
            if previous is None or previous.tag != qn("p") or not has_drawing(previous):
                errors.append(f"图题“{text[:30]}”必须紧邻对应图片下方")
        elif text.startswith("表"):
            following = next_nonblank(blocks, index)
            if following is None or following.tag != qn("tbl"):
                errors.append(f"表题“{text[:30]}”必须紧邻对应表格上方")

    if strict_caption_coverage:
        for index, block in enumerate(blocks):
            if block.tag == qn("p") and has_drawing(block):
                following = next_nonblank(blocks, index)
                if following is None or following.tag != qn("p") or not paragraph_text(following).startswith("图"):
                    errors.append(f"第{index + 1}个正文块中的图片缺少紧邻下方自动图题")
            if block.tag == qn("tbl"):
                previous = previous_nonblank(blocks, index)
                if previous is None or previous.tag != qn("p") or not paragraph_text(previous).startswith("表"):
                    errors.append(f"第{index + 1}个正文块中的表格缺少紧邻上方自动表题")

    if strict_caption_coverage and caption_count == 0:
        errors.append("严格题注检查下至少需要一处图题或表题")

    reference_start: int | None = None
    reference_end = len(blocks)
    for index, block in enumerate(blocks):
        if block.tag != qn("p"):
            continue
        text = re.sub(r"\s+", "", paragraph_text(block))
        if reference_start is None and (text.startswith("11.4参考文献") or text == "参考文献"):
            reference_start = index
        elif reference_start is not None and text.startswith("11.5"):
            reference_end = index
            break

    if reference_start is not None:
        reference_blocks = blocks[reference_start + 1 : reference_end]
        if any(block.tag == qn("tbl") for block in reference_blocks):
            errors.append("11.4参考文献必须使用期刊式普通段落列表，禁止表格")
        numbered_references = 0
        for block in reference_blocks:
            if block.tag != qn("p"):
                continue
            text = paragraph_text(block)
            if re.match(r"^\[\d+\]", text) or block.find("w:pPr/w:numPr", NS) is not None:
                numbered_references += 1
        if final_report and numbered_references == 0:
            errors.append("最终报告的11.4参考文献未识别到顺序编码条目")
    elif final_report:
        errors.append("最终报告未识别到11.4参考文献章节")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="待检查的DOCX")
    parser.add_argument(
        "--strict-caption-coverage",
        action="store_true",
        help="要求每个正文顶层图片/表格都有紧邻的自动题注",
    )
    parser.add_argument(
        "--final-report",
        action="store_true",
        help="要求存在11.4参考文献及顺序编码条目",
    )
    args = parser.parse_args()

    if not args.docx.exists():
        print(f"FAIL\n- 文件不存在：{args.docx}")
        return 2
    if args.docx.suffix.lower() != ".docx":
        print("FAIL\n- 仅支持DOCX文件")
        return 2

    try:
        errors = validate_docx(args.docx, args.strict_caption_coverage, args.final_report)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"FAIL\n- 无法检查DOCX：{exc}")
        return 2

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "PASS: A4页面、页边距、正文/标题/题注样式、域更新和参考文献版式符合预设；"
        "仍须在最终渲染页人工检查字体回退、清晰度、分页和题注视觉位置。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
