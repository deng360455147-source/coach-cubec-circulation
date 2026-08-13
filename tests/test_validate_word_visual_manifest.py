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
    data["pages"][0]["visuals"][0]["lead_in_body_paragraph_present"] = True
    data["pages"][0]["visuals"][0]["contains_embedded_caption"] = False
    data["pages"][0]["visuals"][0]["contains_text"] = True
    data["pages"][0]["visuals"][0]["internal_text_size_pt"] = 12
    return data


class WordVisualManifestTests(unittest.TestCase):
    def test_updated_template_can_form_a_valid_manifest(self) -> None:
        self.assertEqual(validate(production_manifest()), [])

    def test_reference_table_and_caption_drift_fail(self) -> None:
        data = copy.deepcopy(production_manifest())
        data["references"]["uses_table_layout"] = True
        data["captions"]["size_pt"] = 10.5
        errors = "\n".join(validate(data))
        self.assertIn("references.uses_table_layout", errors)
        self.assertIn("captions.size_pt", errors)

    def test_figure_table_toc_and_pagination_drift_fail(self) -> None:
        data = copy.deepcopy(production_manifest())
        visual = data["pages"][0]["visuals"][0]
        visual["lead_in_body_paragraph_present"] = False
        visual["contains_embedded_caption"] = True
        visual["internal_text_size_pt"] = 10.5
        data["table_layout"]["cell_first_line_indent_chars"] = 2
        data["table_of_contents"]["heading_levels"] = [1, 2]
        data["pagination"]["manual_page_breaks_present"] = True
        errors = "\n".join(validate(data))
        self.assertIn("lead_in_body_paragraph_present", errors)
        self.assertIn("contains_embedded_caption", errors)
        self.assertIn("internal_text_size_pt", errors)
        self.assertIn("table_layout.cell_first_line_indent_chars", errors)
        self.assertIn("table_of_contents.heading_levels", errors)
        self.assertIn("pagination.manual_page_breaks_present", errors)


if __name__ == "__main__":
    unittest.main()
