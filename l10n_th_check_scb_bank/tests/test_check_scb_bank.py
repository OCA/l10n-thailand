# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo import tools
from odoo.modules.module import get_resource_path
from odoo.tests.common import Form, SavepointCase


class TestCheckScbBank(SavepointCase):
    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr,
            module,
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load("account", "test", "account_minimal_test.xml")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.layout_scb = cls.env.ref(
            "l10n_th_check_scb_bank.action_report_check_scb_base"
        )
        cls.payment_method_check = cls.env.ref(
            "account_check_printing.account_payment_method_check"
        )
        cls.expenses_journal = cls.browse_ref(cls, "account.expenses_journal")
        cls.bank_journal = cls.browse_ref(cls, "account.bank_journal")

    def _create_invoice(
        self, partner_id, journal_id, invoice_type, price_unit, product_id=False,
    ):
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "type": invoice_type,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "quantity": 1.0,
                        "name": "Advice",
                        "price_unit": price_unit or 0.0,
                    },
                )
            ],
        }
        invoice_id = self.account_move.create(invoice_dict)
        return invoice_id

    def test_01_print_check_scb(self):
        print_unit = 100.0
        invoice_id = self._create_invoice(
            self.partner_1.id, self.expenses_journal.id, "in_invoice", print_unit
        )
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        view_id = "account.view_account_payment_invoice_form"
        with Form(self.account_payment.with_context(ctx), view=view_id) as f:
            f.payment_date = time.strftime("%Y") + "-07-15"
            f.journal_id = self.bank_journal
            f.payment_method_id = self.payment_method_check
        payment = f.save()
        payment.post()
        self.layout_scb.render_qweb_pdf(payment.id)
