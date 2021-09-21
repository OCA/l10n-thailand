# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.tests.common import TransactionCase


class CommonBankPaymentExport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.move_model = self.env["account.move"]
        self.journal_model = self.env["account.journal"]
        self.bank_payment_export_model = self.env["bank.payment.export"]
        self.register_payments_model = self.env["account.payment.register"]
        self.main_company_id = self.env.ref("base.main_company").id
        self.main_currency_id = self.env.ref("base.USD").id
        self.currency_id = self.env.ref("base.EUR").id
        self.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (self.main_currency_id, self.main_company_id),
        )
        self.product_1 = self.env.ref("product.product_product_4")
        self.journal_bank = self.journal_model.search([("type", "=", "bank")], limit=1)
        self.journal_cash = self.journal_model.search([("type", "=", "cash")], limit=1)
        # Create Recipient Bank and default partner
        self.partner_1 = self.env.ref("base.res_partner_2")
        self.partner_2 = self.env.ref("base.res_partner_3")
        self.partner_bank_model = self.env["res.partner.bank"]
        self.bank_bnp = self.env.ref("base.bank_bnp")
        self.bank_ing = self.env.ref("base.bank_ing")
        self.partner_company = self.create_partner_bank(
            "A000-Test", self.env.company.partner_id, self.bank_ing
        )
        self.partner1_bank_bnp = self.create_partner_bank(
            "A001-Test", self.partner_1, self.bank_bnp
        )
        self.partner1_bank_ing = self.create_partner_bank(
            "A002-Test", self.partner_1, self.bank_ing
        )
        self.partner2_bank_ing = self.create_partner_bank(
            "A003-Test", self.partner_2, self.bank_ing
        )

        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        self.payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out"
        )
        self.payment_method_check = self.env.ref(
            "account_check_printing.account_payment_method_check"
        )
        # create invoice to payment
        self.payment1_out_journal_bank = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_out,
            partner=self.partner_1,
            journal=self.journal_bank,
        )
        self.payment2_out_journal_cash = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_out,
            partner=self.partner_1,
            journal=self.journal_cash,
        )
        self.payment3_out_method_check = self.create_invoice_payment(
            amount=200,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_check,
            partner=self.partner_1,
            journal=self.journal_bank,
        )
        self.payment4_out_currency = self.create_invoice_payment(
            amount=300,
            currency_id=self.currency_id,
            payment_method=self.payment_method_manual_out,
            partner=self.partner_1,
            journal=self.journal_bank,
        )
        self.payment5_in = self.create_invoice_payment(
            amount=400,
            inv_type="out_invoice",
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_in,
            partner=self.partner_1,
            journal=self.journal_bank,
        )
        self.payment6_out_partner = self.create_invoice_payment(
            amount=600,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_out,
            partner=self.partner_2,
            journal=self.journal_bank,
        )

    def create_partner_bank(self, acc_number, partner, bank):
        return self.partner_bank_model.create(
            {"acc_number": acc_number, "partner_id": partner.id, "bank_id": bank.id}
        )

    def create_invoice(
        self, amount=100, inv_type="in_invoice", currency_id=None, partner=False
    ):
        """ Returns an open invoice """
        invoice = self.move_model.create(
            {
                "company_id": self.main_company_id,
                "move_type": inv_type,
                "partner_id": partner.id,
                "partner_bank_id": len(partner.bank_ids.ids) == 1
                and partner.bank_ids.id
                or False,
                "currency_id": currency_id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "quantity": 1,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def create_invoice_payment(
        self,
        amount=100,
        inv_type="in_invoice",
        currency_id=None,
        payment_method=False,
        partner=False,
        journal=False,
    ):
        invoice = self.create_invoice(amount, inv_type, currency_id, partner)
        ctx = {"active_model": "account.move", "active_ids": [invoice.id]}
        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "journal_id": journal.id,
                "payment_method_id": payment_method.id,
                "amount": amount,
                "partner_bank_id": invoice.partner_bank_id.id,
                "payment_date": fields.Date.today(),
            }
        )
        payment_list = register_payments.action_create_payments()
        # convert payment list to payment obj
        payment = self.env[payment_list["res_model"]].search(
            [("id", "=", payment_list["res_id"])]
        )
        return payment

    def action_bank_export_excel(self, bank_payment):
        excel_list = bank_payment.action_export_excel_file()
        self.assertEqual(excel_list["report_type"], "xlsx")
        action = self.env.ref("l10n_th_bank_payment_export.action_export_payment_xlsx")
        return action._render_xlsx(
            excel_list["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    excel_list["report_name"],
                    str(excel_list["context"]["active_ids"][0]),
                ),
                "token": "dummy-because-api-expects-one",
            },
        )
