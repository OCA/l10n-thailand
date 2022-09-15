# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SingleTransactionCase


class TestIrSequenceBranchStandard(SingleTransactionCase):
    """A few tests for a 'Standard' sequence."""

    def test_ir_sequence_branch_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        self.env.user.company_id.branch = "00007"
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_branch",
                "name": "Test sequence branch",
                "use_date_range": False,
                "prefix": "test-%(b5)s/%(b4)s/%(b3)s/%(b2)s/%(b1)s-",
                "suffix": "-%(b5)s/%(b4)s/%(b3)s/%(b2)s/%(b1)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

    def test_ir_sequence_branch_2_use(self):
        """Try to use the sequence object."""
        for i in range(1, 10):
            value = self.env["ir.sequence"].next_by_code("test_branch")
            self.assertEqual(
                value, f"test-00007/0007/007/07/7-{i:04}-00007/0007/007/07/7"
            )

    def test_ir_sequence_branch_3_change_branch(self):
        """Change company's branch"""
        self.env.user.company_id.branch = "00314"
        for i in range(10, 20):
            value = self.env["ir.sequence"].next_by_code("test_branch")
            self.assertEqual(
                value, f"test-00314/0314/314/14/4-{i:04}-00314/0314/314/14/4"
            )

    def test_ir_sequence_branch_4_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_branch")])
        seq.unlink()
