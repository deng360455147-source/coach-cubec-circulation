#!/usr/bin/env python3
"""Block internal workflow language from reader-facing Markdown, text, or DOCX."""

from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


START = "<!-- READER_BODY_START -->"
END = "<!-- READER_BODY_END -->"

FORBIDDEN = (
    ("Skill/技能工作流", r"\bskill(?:s)?\b|本技能|教练技能|竞赛教练"),
    ("内部状态码", r"\b(?:DESK_ONLY|READY|BLOCKED|CONDITIONAL|PENDING|PASS|FAIL)\b|MODEL_SELECTION_[A-Z_]+|AWAITING_USER_APPROVAL|UNSUPPORTED_CLAIMS"),
    ("内部批次码", r"\bB0[123](?:[_-][A-Z0-9_.-]+)?\b"),
    ("程序或文件路径", r"\.ipynb\b|\.py\b|(?:^|[\s`'\"])(?:analysis|scripts|assets|references)/|SKILL\.md|/Users/|/var/|/tmp/|[A-Z]:\\"),
    ("工具调用名", r"\$[A-Za-z0-9][A-Za-z0-9:_-]*|Notebook"),
    ("内部证据编号", r"(?<![A-Za-z0-9])E\d{3,}(?![A-Za-z0-9])|证据\s*ID"),
    ("内部占位状态", r"\[(?:待调研|待核验|待验证假设|团队判断|结构项|已核验:[^\]]+|待团队核实[^\]]*)\]"),
    ("生产过程叙述", r"按照最新版教练|程序分析使用|程序已经运行|本稿状态为|调用(?:了|以下)?(?:工具|插件|技能)|AI生成|模型记忆|系统提示"),
    ("第一二人称", r"(?:^|[。！？；\n])\s*(?:我们|我认为|笔者|你可以看到)"),
)

SUMMARY_COLON_PATTERN = re.compile(
    r"(?:由[^。！？\n：]{0,18}(?:构成|组成)|包括|包含|分为|来自|"
    r"主要(?:有|包括|体现为|表现为)|可(?:设计|采取|实施|形成)|"
    r"缺口(?:同样)?明确|如下|分别(?:为|是))[^。！？\n：]{0,36}："
    r"(?=[^。！？\n]{0,220}(?:、|；|，)[^。！？\n]{0,220}(?:、|；|，))"
)
QUOTED_TEXT_PATTERN = re.compile(r"“([^”\n]{2,100})”|\"([^\"\n]{2,100})\"")
CHAIN_CONNECTOR_PATTERN = re.compile(r"—|→|->|/|＋|\+|、")
EMPTY_GRANDIOSE_PATTERN = re.compile(
    r"比比皆是|毋庸置疑|令人惊叹|不可磨灭(?:的贡献)?|"
    r"范式转移|全方位赋能|打造(?:了)?(?:一个)?闭环生态|"
    r"实现了?跨越式发展|耦合内聚|切中要害"
)
LONG_ATTRIBUTIVE_PATTERN = re.compile(
    r"一个[^，。；！？\n]{0,20}的"
    r"[^，。；！？\n]{0,20}的"
    r"[^，。；！？\n]{0,20}的"
)
MECHANICAL_SEQUENCE_PATTERN = re.compile(
    r"首先[^。！？\n]{0,180}其次[^。！？\n]{0,180}(?:最后|再次)"
)


def extract_markdown_body(text: str) -> str:
    if START in text or END in text:
        if START not in text or END not in text or text.index(START) >= text.index(END):
            raise ValueError("reader body markers are incomplete or out of order")
        text = text.split(START, 1)[1].split(END, 1)[0]
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def extract_docx_text(path: Path) -> str:
    document_parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name == "word/document.xml"
            or re.fullmatch(r"word/(?:header|footer)\d+\.xml", name)
            or name in {"word/footnotes.xml", "word/endnotes.xml"}
        ]
        if "word/document.xml" not in names:
            raise ValueError("DOCX does not contain word/document.xml")
        for name in names:
            root = ET.fromstring(archive.read(name))
            paragraphs: list[str] = []
            for paragraph in (node for node in root.iter() if node.tag.endswith("}p")):
                parts: list[str] = []
                for node in paragraph.iter():
                    if node.tag.endswith("}t") and node.text:
                        parts.append(node.text)
                    elif node.tag.endswith("}tab"):
                        parts.append("\t")
                    elif node.tag.endswith("}br"):
                        parts.append("\n")
                if parts:
                    paragraphs.append("".join(parts))
            document_parts.append("\n".join(paragraphs))
    return "\n".join(part for part in document_parts if part)


def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return extract_docx_text(path)
    if suffix in {".md", ".txt"}:
        return extract_markdown_body(path.read_text(encoding="utf-8"))
    raise ValueError("supported inputs are .md, .txt, and .docx")


def snippet(text: str, start: int, end: int) -> str:
    value = re.sub(r"\s+", " ", text[max(0, start - 35) : min(len(text), end + 35)])
    return value[:140]


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    for label, pattern in FORBIDDEN:
        matches = list(re.finditer(pattern, text, flags=re.MULTILINE | re.IGNORECASE))
        for match in matches[:5]:
            errors.append(f"{label}: …{snippet(text, match.start(), match.end())}…")
        if len(matches) > 5:
            errors.append(f"{label}: 另有 {len(matches) - 5} 处")
    if re.search(r"【[^】]*】", text):
        errors.append("未替换占位符: 正文仍含有【…】")
    summary_matches = list(SUMMARY_COLON_PATTERN.finditer(text))
    for match in summary_matches[:5]:
        errors.append(
            f"冒号式概括串列: …{snippet(text, match.start(), match.end())}…"
        )
    if len(summary_matches) > 5:
        errors.append(f"冒号式概括串列: 另有 {len(summary_matches) - 5} 处")
    quote_chain_matches: list[re.Match[str]] = []
    for match in QUOTED_TEXT_PATTERN.finditer(text):
        content = match.group(1) or match.group(2) or ""
        if len(CHAIN_CONNECTOR_PATTERN.findall(content)) >= 2:
            quote_chain_matches.append(match)
    for match in quote_chain_matches[:5]:
        errors.append(
            f"引号式词组链: …{snippet(text, match.start(), match.end())}…"
        )
    if len(quote_chain_matches) > 5:
        errors.append(f"引号式词组链: 另有 {len(quote_chain_matches) - 5} 处")
    style_paragraphs = [
        paragraph.strip()
        for paragraph in text.splitlines()
        if paragraph.strip()
        and not paragraph.lstrip().startswith(("#", "|", "资料来源：", "资料来源:", "[参考文献]"))
        and not re.match(r"^\[\d+\]", paragraph.strip())
    ]
    style_text = "\n".join(style_paragraphs)
    for label, pattern in (
        ("空泛渲染表达", EMPTY_GRANDIOSE_PATTERN),
        ("欧化长定语", LONG_ATTRIBUTIVE_PATTERN),
        ("机械顺序连接", MECHANICAL_SEQUENCE_PATTERN),
    ):
        matches = list(pattern.finditer(style_text))
        for match in matches[:5]:
            errors.append(f"{label}: …{snippet(style_text, match.start(), match.end())}…")
        if len(matches) > 5:
            errors.append(f"{label}: 另有 {len(matches) - 5} 处")
    return errors


def make_minimal_docx(path: Path, text: str) -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def self_test() -> int:
    clean = (
        "数据显示，该企业收入结构在三年内发生变化。资料来源：企业2025年度报告，第37页。"
        "企业先识别不同层级的需求，再开展小范围试销，并根据销售表现滚动补货。"
        "文中所称“长沙中枢”仅表示待验证的区域场景。"
    )
    if validate_text(clean):
        print("FAIL: clean report text was rejected")
        return 1
    bad = (
        "本研究采用纯案头分析模式 DESK_ONLY。程序分析使用 analysis/B01_test.ipynb。"
        "Notebook 已执行。按照最新版教练 Skill，方法达到 READY；本稿状态为 "
        "MODEL_SELECTION_BLOCKED。（E016）"
    )
    bad_errors = validate_text(bad)
    required_labels = {"Skill/技能工作流", "内部状态码", "内部批次码", "程序或文件路径", "工具调用名", "内部证据编号", "生产过程叙述"}
    found_labels = {error.split(":", 1)[0] for error in bad_errors}
    if not required_labels.issubset(found_labels):
        print(f"FAIL: internal workflow text was not fully detected: {sorted(required_labels - found_labels)}")
        return 1
    prose_bad = (
        "企业的价值主张由四个支点构成：高质价比、丰富品类、高频上新和便利门店体验。"
        "企业执行“分层需求—小范围验证—滚动补货—退出复盘”。"
        "首先检查收入，其次比较成本，最后得出结论。"
        "这是一个能够系统识别区域门店需求的具有战略意义的不可磨灭的贡献。"
    )
    prose_errors = validate_text(prose_bad)
    prose_labels = {error.split(":", 1)[0] for error in prose_errors}
    for required in (
        "冒号式概括串列",
        "引号式词组链",
        "机械顺序连接",
        "欧化长定语",
        "空泛渲染表达",
    ):
        if required not in prose_labels:
            print(f"FAIL: {required} was not detected")
            return 1
    with tempfile.TemporaryDirectory() as temp_dir:
        docx = Path(temp_dir) / "test.docx"
        make_minimal_docx(docx, "程序分析使用 test.ipynb")
        if not validate_text(extract_docx_text(docx)):
            print("FAIL: DOCX extraction did not expose forbidden text")
            return 1
    print("PASS: reader-facing report validator self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查读者版报告是否泄漏内部工作流，或出现高风险的机械化中文表达"
    )
    parser.add_argument("report", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.report is None:
        parser.error("report is required unless --self-test is used")
    try:
        text = load_text(args.report)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"FAIL\n- 无法读取正文：{exc}")
        return 2
    errors = validate_text(text)
    if errors:
        print("FAIL: 读者正文包含内部工作流语言、未替换内容或禁用表达")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 读者正文未发现内部工作流泄漏、占位符或高风险机械化表达")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
