# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, tools
from odoo.modules.module import get_resource_path
from odoo.tests.common import Form, SavepointCase


class TestCheckKtb(SavepointCase):
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
        Journal = cls.env["account.journal"]
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.account_payment_register = cls.env["account.payment.register"]
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.layout_ktb = cls.env.ref("l10n_th_check_ktb.action_report_check_ktb_base")
        cls.payment_method_check = cls.env.ref(
            "account_check_printing.account_payment_method_check"
        )
        cls.expenses_journal = Journal.search([("type", "=", "purchase")])[0]
        cls.bank_journal = Journal.search([("type", "=", "bank")])[0]

    def _create_invoice(
        self,
        partner_id,
        journal_id,
        invoice_type,
        price_unit,
        product_id=False,
    ):
        invoice_dict = {
            "name": "Test Supplier Invoice",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": invoice_type,
            "invoice_date": fields.Date.today(),
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

    def test_01_print_check_ktb(self):
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
        view_id = "account.view_account_payment_register_form"
        with Form(self.account_payment_register.with_context(ctx), view=view_id) as f:
            f.journal_id = self.bank_journal
            f.payment_method_id = self.payment_method_check
        payment_register = f.save()
        payment = payment_register._create_payments()
        self.assertEqual(payment.state, "posted")
        self.layout_ktb._render_qweb_pdf(payment.id)
