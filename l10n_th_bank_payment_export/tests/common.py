# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo_test_helper import FakeModelLoader

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class CommonBankPaymentExport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .bank_payment_export_tester import (
            BankPaymentExportTester,
            BankPaymentTemplateTester,
        )

        cls.loader.update_registry((BankPaymentExportTester, BankPaymentTemplateTester))

        cls.move_model = cls.env["account.move"]
        cls.journal_model = cls.env["account.journal"]
        cls.bank_payment_template_model = cls.env["bank.payment.template"]
        cls.bank_payment_export_model = cls.env["bank.payment.export"]
        cls.field_model = cls.env["ir.model.fields"]
        cls.register_payments_model = cls.env["account.payment.register"]
        cls.main_company_id = cls.env.ref("base.main_company").id
        cls.main_currency_id = cls.env.ref("base.USD").id
        # Active multi-currency
        currency_EUR = cls.env.ref("base.EUR")
        currency_EUR.active = True
        cls.currency_id = currency_EUR.id
        cls.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (cls.main_currency_id, cls.main_company_id),
        )
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.journal_bank = cls.journal_model.search([("type", "=", "bank")], limit=1)
        cls.journal_cash = cls.journal_model.search([("type", "=", "cash")], limit=1)
        # Create Recipient Bank and default partner
        cls.partner_1 = cls.env.ref("base.res_partner_2")
        cls.partner_2 = cls.env.ref("base.res_partner_3")
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.bank_bnp = cls.env.ref("base.bank_bnp")
        cls.bank_ing = cls.env.ref("base.bank_ing")
        cls.partner_company = cls.create_partner_bank(
            cls, "A000Test", cls.env.company.partner_id, cls.bank_ing
        )
        cls.partner1_bank_bnp = cls.create_partner_bank(
            cls, "A001Test", cls.partner_1, cls.bank_bnp
        )
        cls.partner1_bank_ing = cls.create_partner_bank(
            cls, "A002Test", cls.partner_1, cls.bank_ing
        )
        cls.partner2_bank_ing = cls.create_partner_bank(
            cls, "A003Test", cls.partner_2, cls.bank_ing
        )

        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        cls.payment_method_manual_out = cls.env.ref(
            "account.account_payment_method_manual_out"
        )

        cls.journal_bank_manual_out = (
            cls.journal_bank.outbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id == cls.payment_method_manual_out
            )
        )
        cls.journal_bank_manual_in = (
            cls.journal_bank.inbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id == cls.payment_method_manual_in
            )
        )
        cls.journal_cash_manual_out = (
            cls.journal_cash.outbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id == cls.payment_method_manual_out
            )
        )

        # create invoice to payment
        cls.payment1_out_journal_bank = cls.create_invoice_payment(
            cls,
            amount=100,
            currency_id=cls.main_currency_id,
            payment_method=cls.journal_bank_manual_out,
            partner=cls.partner_1,
            journal=cls.journal_bank,
            init=True,
        )
        cls.payment2_out_journal_cash = cls.create_invoice_payment(
            cls,
            amount=100,
            currency_id=cls.main_currency_id,
            payment_method=cls.journal_cash_manual_out,
            partner=cls.partner_1,
            journal=cls.journal_cash,
            init=True,
        )
        cls.payment4_out_currency = cls.create_invoice_payment(
            cls,
            amount=300,
            currency_id=cls.currency_id,
            payment_method=cls.journal_bank_manual_out,
            partner=cls.partner_1,
            journal=cls.journal_bank,
            init=True,
        )
        cls.payment5_in = cls.create_invoice_payment(
            cls,
            amount=400,
            inv_type="out_invoice",
            currency_id=cls.main_currency_id,
            payment_method=cls.journal_bank_manual_in,
            partner=cls.partner_1,
            journal=cls.journal_bank,
            init=True,
        )
        cls.payment6_out_partner = cls.create_invoice_payment(
            cls,
            amount=600,
            currency_id=cls.main_currency_id,
            payment_method=cls.journal_bank_manual_out,
            partner=cls.partner_2,
            journal=cls.journal_bank,
            init=True,
        )

    def create_partner_bank(self, acc_number, partner, bank):
        return self.partner_bank_model.create(
            {"acc_number": acc_number, "partner_id": partner.id, "bank_id": bank.id}
        )

    def create_invoice(
        self, amount=100, inv_type="in_invoice", currency_id=None, partner=False
    ):
        """Returns an open invoice"""
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
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [],
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
        is_export=False,
        bank_payment_template_id=False,
        multi=False,
        init=False,
    ):
        loop = 2 if multi else 1
        invoices = self.move_model
        for _i in range(loop):
            # For init class
            if init:
                invoice = self.create_invoice(
                    self, amount, inv_type, currency_id, partner
                )
            else:
                invoice = self.create_invoice(amount, inv_type, currency_id, partner)
            invoices += invoice
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register_payments = self.register_payments_model.with_context(**ctx).create(
            {
                "journal_id": journal.id,
                "payment_method_line_id": payment_method.id,
                "amount": amount,
                "partner_bank_id": invoices.mapped("partner_bank_id").id,
                "payment_date": fields.Date.today(),
                "is_export": is_export,
                "bank_payment_template_id": bank_payment_template_id,
            }
        )
        payment_list = register_payments.action_create_payments()
        domain = ("id", "=", payment_list.get("res_id", False))
        if not payment_list.get("res_id", False):
            domain = ("id", "in", payment_list["domain"][0][2])
        # convert payment list to payment obj
        payment = self.env[payment_list["res_model"]].search([domain])
        return payment

    def action_bank_export_excel(self, bank_payment):
        excel_list = bank_payment.action_export_excel_file()
        self.assertEqual(excel_list["report_type"], "xlsx")
        action = self.env.ref("l10n_th_bank_payment_export.action_export_payment_xlsx")
        return action._render_xlsx(
            action.report_name,
            excel_list["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    excel_list["report_name"],
                    str(excel_list["context"]["active_ids"][0]),
                ),
                "token": "dummy-because-api-expects-one",
            },
        )

    def create_bank_payment_template(self, bank, data_dict):
        """This function is common create template, Format of data_dict is
        [
            {
                'field_id': field_id,
                'value': value,
            },
            {
                'field_id': field_id,
                'value': value,
            }
        ]
        """
        template = self.bank_payment_template_model.create(
            {
                "name": "Test Template %(bank)s"
                % {
                    "bank": bank,
                },
                "bank": bank,
                "template_config_line": [
                    Command.create(
                        {
                            "field_id": data.get("field_id"),
                            "value": data.get("value"),
                        }
                    )
                    for data in data_dict
                ],
            }
        )
        return template
