from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_word_visual_manifest import validate


ROOT = Path(__file__).resolve().parents[1]


def production_manifest() -> dict:
    data = json.loads((ROOT / "assets/word-visual-manifest-template.json").read_text(encoding="utf-8"))
    data["template_mode"] = False
    data["document_id"] = "B01-V1"
    data["source_report_version"] = "V1"
    data["docx_file"] = "B01.docx"
    data["visual_map_file"] = "不适用"
    data["rendered_pdf"] = "B01.pdf"
    data["pages"][0]["chapter"] = "第3章 引言"
    data["pages"][0]["page_role"] = "narrative"
    data["pages"][0]["visuals"][0]["kind"] = "image"
    data["pages"][0]["visuals"][0]["subtype"] = "research-framework"
    return data


class WordVisualManifestTests(unittest.TestCase):
    def test_updated_template_can_form_a_valid_manifest(self) -> None:
        self.assertEqual(validate(production_manifest()), [])

    def test_reference_table_and_caption_drift_fail(self) -> None:
        data = copy.deepcopy(production_manifest())
        data["references"]["uses_table_layout"] = True
        data["captions"]["size_pt"] = 9
        errors = "\n".join(validate(data))
        self.assertIn("references.uses_table_layout", errors)
        self.assertIn("captions.size_pt", errors)


if __name__ == "__main__":
    unittest.main()
