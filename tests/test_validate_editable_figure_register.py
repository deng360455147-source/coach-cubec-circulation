from __future__ import annotations

import copy
import unittest

from scripts.validate_editable_figure_register import make_self_test_data, validate


class EditableFigureRegisterTests(unittest.TestCase):
    def test_committed_canva_master_passes(self) -> None:
        self.assertEqual(validate(make_self_test_data(), for_production=True), [])

    def test_missing_commit_approval_fails(self) -> None:
        data = copy.deepcopy(make_self_test_data())
        data["figures"][0]["canva"]["user_commit_approval_recorded"] = False
        errors = "\n".join(validate(data, for_production=True))
        self.assertIn("user_commit_approval_recorded", errors)

    def test_canva_request_needs_committed_canva_master(self) -> None:
        data = copy.deepcopy(make_self_test_data())
        figure = data["figures"][0]
        figure["editability_mode"] = "EXCALIDRAW_MASTER"
        figure["editable_master_location"] = "figure.excalidraw"
        figure["word_editability"] = "rendered-in-word-editable-in-source"
        figure["canva"]["status"] = "AWAITING_DESIGN_ID"
        errors = "\n".join(validate(data, for_production=True))
        self.assertIn("没有已提交的CANVA_MASTER", errors)


if __name__ == "__main__":
    unittest.main()
