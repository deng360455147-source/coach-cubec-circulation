#!/usr/bin/env python3
"""Validate editable masters for figures inserted into a CUBEC Word report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_MODES = {
    "WORD_NATIVE",
    "CANVA_MASTER",
    "EXCALIDRAW_MASTER",
    "THESIS_SOURCE",
    "REPRODUCIBLE_DATA_CHART",
    "ORIGINAL_EVIDENCE_RASTER",
}
EXPECTED_WORD_EDITABILITY = {
    "WORD_NATIVE": "editable-in-word",
    "CANVA_MASTER": "rendered-in-word-editable-in-canva",
    "EXCALIDRAW_MASTER": "rendered-in-word-editable-in-source",
    "THESIS_SOURCE": "rendered-in-word-editable-in-source",
    "REPRODUCIBLE_DATA_CHART": "rendered-in-word-editable-in-source",
    "ORIGINAL_EVIDENCE_RASTER": "not-editable-original-evidence",
}
QA_KEYS = (
    "editable_master_opens",
    "word_render_matches_master",
    "caption_and_source_match",
    "minimum_text_size_checked",
    "rebuild_tested",
)
CHECK_KEYS = (
    "all_word_figures_registered",
    "all_generated_figures_have_editable_masters",
    "original_raster_exceptions_documented",
    "canva_transactions_followed_approval_gate",
    "word_revalidated_after_master_updates",
)


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_text(item) for item in value)


def validate(data: Any, for_production: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["根对象必须是JSON对象"]
    if data.get("template_mode") is not False:
        errors.append("template_mode 必须改为 false")
    for key in ("schema_version", "document_id", "word_file"):
        if not nonempty_text(data.get(key)):
            errors.append(f"{key} 必须是非空字符串")
    canva_requested = data.get("canva_requested_for_this_document")
    if not isinstance(canva_requested, bool):
        errors.append("canva_requested_for_this_document 必须是布尔值")
        canva_requested = False

    figures = data.get("figures")
    if not isinstance(figures, list) or not figures:
        errors.append("figures 必须是非空数组")
        figures = []
    ids: set[str] = set()
    canva_master_count = 0
    for index, figure in enumerate(figures):
        where = f"figures[{index}]"
        if not isinstance(figure, dict):
            errors.append(f"{where} 必须是对象")
            continue
        figure_id = figure.get("figure_id")
        if not nonempty_text(figure_id):
            errors.append(f"{where}.figure_id 必须是非空字符串")
        elif figure_id in ids:
            errors.append(f"{where}.figure_id 重复：{figure_id}")
        else:
            ids.add(figure_id)
        for key in ("word_caption", "word_render_file", "editable_master_location", "rebuild_instructions"):
            if not nonempty_text(figure.get(key)):
                errors.append(f"{where}.{key} 必须是非空字符串")
        if not nonempty_text_list(figure.get("source_ids")):
            errors.append(f"{where}.source_ids 至少包含一个来源ID")
        if not isinstance(figure.get("source_data"), list):
            errors.append(f"{where}.source_data 必须是数组")

        mode = figure.get("editability_mode")
        if mode not in ALLOWED_MODES:
            errors.append(f"{where}.editability_mode 必须属于 {sorted(ALLOWED_MODES)}")
            continue
        expected = EXPECTED_WORD_EDITABILITY[mode]
        if figure.get("word_editability") != expected:
            errors.append(f"{where}.word_editability 在 {mode} 模式下必须为 {expected}")
        location = str(figure.get("editable_master_location", "")).lower()
        if mode == "WORD_NATIVE" and not location.endswith(".docx"):
            errors.append(f"{where}.editable_master_location 在WORD_NATIVE模式下必须指向DOCX")
        elif mode == "EXCALIDRAW_MASTER" and not location.endswith(".excalidraw"):
            errors.append(f"{where}.editable_master_location 必须指向.excalidraw源文件")
        elif mode == "THESIS_SOURCE" and not location.endswith((".tex", ".drawio")):
            errors.append(f"{where}.editable_master_location 必须指向.tex或.drawio源文件")
        elif mode == "REPRODUCIBLE_DATA_CHART":
            if not location.endswith((".ipynb", ".xlsx", ".xlsm", ".py", ".r")):
                errors.append(f"{where}.editable_master_location 必须指向可复现图表源文件")
            if not nonempty_text_list(figure.get("source_data")):
                errors.append(f"{where}.source_data 在数据图模式下不能为空")

        canva = figure.get("canva")
        if not isinstance(canva, dict):
            errors.append(f"{where}.canva 必须是对象")
            canva = {}
        if mode == "CANVA_MASTER":
            canva_master_count += 1
            if canva.get("status") != "COMMITTED":
                errors.append(f"{where}.canva.status 必须为 COMMITTED")
            design_id = canva.get("design_id")
            if not nonempty_text(design_id) or not str(design_id).startswith("D"):
                errors.append(f"{where}.canva.design_id 必须是以D开头的设计ID")
            page_index = canva.get("page_index")
            if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
                errors.append(f"{where}.canva.page_index 必须是非负整数")
            if not nonempty_text_list(canva.get("element_ids")):
                errors.append(f"{where}.canva.element_ids 至少包含一个元素ID")
            for key in (
                "responsive_page_checked",
                "user_commit_approval_recorded",
                "transaction_committed",
            ):
                if canva.get(key) is not True:
                    errors.append(f"{where}.canva.{key} 必须为 true")
            if not nonempty_text(canva.get("edit_link")):
                errors.append(f"{where}.canva.edit_link 必须是非空字符串")
        else:
            if canva.get("status") not in {"NOT_APPLICABLE", "AWAITING_DESIGN_ID"}:
                errors.append(f"{where}.canva.status 在非Canva模式下必须为 NOT_APPLICABLE 或 AWAITING_DESIGN_ID")

        qa = figure.get("qa")
        if not isinstance(qa, dict):
            errors.append(f"{where}.qa 必须是对象")
        else:
            for key in QA_KEYS:
                if qa.get(key) is not True:
                    errors.append(f"{where}.qa.{key} 必须为 true")

    if for_production and canva_requested and canva_master_count < 1:
        errors.append("用户要求Canva可编辑母版，但登记表中没有已提交的CANVA_MASTER")

    checks = data.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks 必须是对象")
    else:
        for key in CHECK_KEYS:
            if checks.get(key) is not True:
                errors.append(f"checks.{key} 必须为 true")
    return errors


def make_self_test_data() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "template_mode": False,
        "document_id": "B02-V1",
        "word_file": "B02.docx",
        "canva_requested_for_this_document": True,
        "figures": [
            {
                "figure_id": "FIG-5-1",
                "word_caption": "区域门店结构",
                "word_render_file": "figure-5-1.svg",
                "editability_mode": "CANVA_MASTER",
                "editable_master_location": "https://www.canva.com/design/D123/example",
                "word_editability": "rendered-in-word-editable-in-canva",
                "source_ids": ["E001"],
                "source_data": [],
                "rebuild_instructions": "在Canva更新既有元素后重新导出并替换Word图",
                "canva": {
                    "status": "COMMITTED",
                    "design_id": "D123",
                    "page_index": 0,
                    "element_ids": ["element-1"],
                    "responsive_page_checked": True,
                    "user_commit_approval_recorded": True,
                    "transaction_committed": True,
                    "edit_link": "https://www.canva.com/design/D123/example",
                },
                "qa": {key: True for key in QA_KEYS},
            }
        ],
        "checks": {key: True for key in CHECK_KEYS},
    }


def self_test() -> int:
    data = make_self_test_data()
    if validate(data, for_production=True):
        print("FAIL: valid Canva editable register was rejected")
        return 1
    data = make_self_test_data()
    data["figures"][0]["canva"]["user_commit_approval_recorded"] = False
    errors = validate(data, for_production=True)
    if not any("user_commit_approval_recorded" in error for error in errors):
        print("FAIL: missing Canva commit approval was not detected")
        return 1
    data = make_self_test_data()
    data["figures"][0]["editability_mode"] = "EXCALIDRAW_MASTER"
    data["figures"][0]["editable_master_location"] = "figure.excalidraw"
    data["figures"][0]["word_editability"] = "rendered-in-word-editable-in-source"
    data["figures"][0]["canva"] = {
        "status": "AWAITING_DESIGN_ID",
        "design_id": None,
        "page_index": None,
        "element_ids": [],
        "responsive_page_checked": False,
        "user_commit_approval_recorded": False,
        "transaction_committed": False,
        "edit_link": None,
    }
    errors = validate(data, for_production=True)
    if not any("没有已提交的CANVA_MASTER" in error for error in errors):
        print("FAIL: missing requested Canva master was not detected")
        return 1
    print("PASS: editable figure register validator self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="校验Word配图是否保留真实可编辑母版")
    parser.add_argument("register", nargs="?", type=Path)
    parser.add_argument("--for-production", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.register is None:
        parser.error("register is required unless --self-test is used")
    try:
        data = json.loads(args.register.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL\n- 文件不存在：{args.register}")
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
    print("PASS: Word配图均有可编辑母版或已记录不可编辑的原始证据例外")
    return 0


if __name__ == "__main__":
    sys.exit(main())
