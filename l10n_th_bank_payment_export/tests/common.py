# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo_test_helper import FakeModelLoader

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class CommonBankPaymentExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .bank_payment_export_tester import (
            BankExportFormatTester,
            BankPaymentExportTester,
            BankPaymentTemplateTester,
        )

        cls.loader.update_registry(
            (BankPaymentExportTester, BankPaymentTemplateTester, BankExportFormatTester)
        )

        cls.other_currency = cls.setup_other_currency("EUR")

        cls.bank_export_format_model = cls.env["bank.export.format"]
        cls.bank_payment_export_model = cls.env["bank.payment.export"]
        cls.bank_payment_template_model = cls.env["bank.payment.template"]
        cls.field_model = cls.env["ir.model.fields"]
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.register_payments_model = cls.env["account.payment.register"]

        cls.partner_1 = cls.env.ref("base.res_partner_2")
        cls.partner_2 = cls.env.ref("base.res_partner_3")
        cls.bank_bnp = cls.env.ref("base.bank_bnp")
        cls.bank_ing = cls.env.ref("base.bank_ing")

        cls.partner_company = cls.create_partner_bank(
            cls, "A000-Test", cls.env.company.partner_id, cls.bank_ing
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

        cls.bill_partner1_1 = cls.init_invoice(
            "in_invoice",
            partner=cls.partner_1,
            amounts=[100.0],
            post=True,
        )
        cls.bill_partner1_2 = cls.init_invoice(
            "in_invoice",
            partner=cls.partner_1,
            amounts=[200.0],
            post=True,
        )
        cls.bill_partner1_currency = cls.init_invoice(
            "in_invoice",
            partner=cls.partner_1,
            amounts=[100.0],
            post=True,
            currency=cls.other_currency,
        )
        cls.bill_partner2 = cls.init_invoice(
            "in_invoice",
            partner=cls.partner_2,
            amounts=[100.0],
            post=True,
        )
        cls.inv_partner1 = cls.init_invoice(
            "out_invoice",
            partner=cls.partner_1,
            amounts=[100.0],
            post=True,
        )

    def create_partner_bank(self, acc_number, partner, bank):
        return self.partner_bank_model.create(
            {"acc_number": acc_number, "partner_id": partner.id, "bank_id": bank.id}
        )

    def action_bank_export_excel(self, bank_payment):
        excel_list = bank_payment.action_export_excel_file()
        self.assertEqual(excel_list["report_type"], "xlsx")
        # action = \
        #     self.env.ref("l10n_th_bank_payment_export.action_export_payment_xlsx")
        # return action._render_xlsx(
        #     excel_list["context"]["active_ids"],
        #     {
        #         "data": "['/report/xlsx/{}/{}','xlsx']".format(
        #             excel_list["report_name"],
        #             str(excel_list["context"]["active_ids"][0]),
        #         ),
        #         "token": "dummy-because-api-expects-one",
        #     },
        # )

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
                "name": f"Test Template {bank}",
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

    def create_payment_from_invoice(self, invoices, post=False):
        register_payment = self.register_payments_model.with_context(
            active_model="account.move", active_ids=invoices.ids
        ).create(
            {
                "payment_date": invoices[0].date,
            }
        )
        if post:
            register_payment = register_payment._create_payments()
        return register_payment
