# Copyright 2023 Ecosoft Co., Ltd. (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseGuaranteeSequenceOption(TransactionCase):
    def setUp(self):
        super(TestPurchaseGuaranteeSequenceOption, self).setUp()
        self.PurchaseGuarantee = self.env["purchase.guarantee"]
        self.pg_vals = {
            "amount": 200.0,
            "document_ref": "Ref.",
        }
        self.pg_seq_opt = self.env.ref(
            "l10n_th_gov_purchase_guarantee_sequence_option.purchase_guarantee_sequence_option"
        )

    def test_purchase_guarantee_sequence_options(self):
        """test with and without sequence option activated"""
        # With sequence option
        self.pg_seq_opt.use_sequence_option = True
        self.pg = self.PurchaseGuarantee.create(self.pg_vals.copy())
        self.assertIn("PG-1", self.pg.name)
        self.pg_copy = self.pg.copy()
        self.assertIn("PG-1", self.pg_copy.name)
        # Without sequence option
        self.pg_seq_opt.use_sequence_option = False
        self.pg = self.PurchaseGuarantee.create(self.pg_vals.copy())
        self.assertNotIn("PG-1", self.pg.name)
        self.pg_copy = self.pg.copy()
        self.assertNotIn("PG-1", self.pg_copy.name)
