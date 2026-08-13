from __future__ import annotations

import unittest

from scripts.validate_reader_facing_report import validate_text


class ReaderFacingReportStyleTests(unittest.TestCase):
    def test_normal_subject_predicate_object_prose_passes(self) -> None:
        text = (
            "企业通过集中采购减少中间流通环节，仓配网络则缩短了补货路径。"
            "数字系统使总部和门店能够及时掌握销售与库存变化。"
            "资料来源：企业2025年度报告，第37页。"
        )
        self.assertEqual(validate_text(text), [])

    def test_summary_colon_list_is_rejected(self) -> None:
        errors = "\n".join(
            validate_text(
                "价值创造来自四个方面：集中采购减少流通层级，仓网缩短补货路径，"
                "数字系统提高库存可视性，加盟网络扩大终端覆盖。"
            )
        )
        self.assertIn("冒号式概括串列", errors)

    def test_quoted_phrase_chain_is_rejected(self) -> None:
        errors = "\n".join(
            validate_text("企业执行“分层需求—小范围验证—滚动补货—退出复盘”。")
        )
        self.assertIn("引号式词组链", errors)

    def test_single_quoted_term_is_allowed(self) -> None:
        self.assertEqual(
            validate_text("本节将“长沙中枢”作为有待验证的区域经营场景。"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
