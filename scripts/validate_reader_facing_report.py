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


def extract_markdown_body(text: str) -> str:
    if START in text or END in text:
        if START not in text or END not in text or text.index(START) >= text.index(END):
            raise ValueError("reader body markers are incomplete or out of order")
        text = text.split(START, 1)[1].split(END, 1)[0]
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def extract_docx_text(path: Path) -> str:
    parts: list[str] = []
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
            for node in root.iter():
                if node.tag.endswith("}t") and node.text:
                    parts.append(node.text)
                elif node.tag.endswith("}tab"):
                    parts.append("\t")
                elif node.tag.endswith("}br"):
                    parts.append("\n")
    return " ".join(parts)


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
    clean = "数据显示，该企业收入结构在三年内发生变化。资料来源：企业2025年度报告，第37页。"
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
        description="检查读者版报告是否泄漏内部Skill、状态码、路径、证据编号和占位符"
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
        print("FAIL: 读者正文包含内部工作流语言或未替换内容")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 读者正文未发现Skill、状态码、程序路径、内部证据编号或占位符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
