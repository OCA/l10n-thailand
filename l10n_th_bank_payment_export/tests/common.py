# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

#: Bank key used by the test suite to add a temporary "TEST" selection.
TEST_BANK_KEY = "TEST"
TEST_BANK_LABEL = "Test Bank"


@tagged("post_install", "-at_install")
class CommonBankPaymentExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.other_currency = cls.setup_other_currency("EUR")

        cls.bank_payment_export_model = cls.env["bank.payment.export"]
        cls.bank_template_model = cls.env["bank.template"]
        cls.bank_payment_profile_model = cls.env["bank.payment.profile"]
        cls.field_model = cls.env["ir.model.fields"]
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.register_payments_model = cls.env["account.payment.register"]

        # Add a "TEST" bank key to the relevant Selection fields so that test
        # fixtures (profiles, templates, exports) can use it without requiring a
        # bank-specific extension module. The original selections are restored
        # in tearDownClass.
        cls._original_selections = {}
        for model in (
            cls.bank_payment_export_model,
            cls.bank_template_model,
            cls.bank_payment_profile_model,
        ):
            field = model._fields["bank"]
            cls._original_selections[model._name] = {
                "selection": list(field.selection),
                "_selection": (
                    dict(field._selection) if field._selection is not None else None
                ),
            }
            new_selection = [
                *(field.selection if isinstance(field.selection, list) else []),
                (TEST_BANK_KEY, TEST_BANK_LABEL),
            ]
            field.selection = new_selection
            field._selection = {kv[0]: kv[1] for kv in new_selection}

        cls.partner_1 = cls.env.ref("base.res_partner_2")
        cls.partner_2 = cls.env.ref("base.res_partner_3")
        cls.bank_bnp = cls.env.ref("base.bank_bnp")
        cls.bank_ing = cls.env.ref("base.bank_ing")

        cls.partner_company = cls.create_partner_bank(
            cls, "A000-Test", cls.env.company.partner_id, cls.bank_ing
        )
        # Company bank account must be trusted to post out_invoice.
        cls.partner_company.allow_out_payment = True
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

    @classmethod
    def tearDownClass(cls):
        # Restore the original Selection values.
        for model_name, original in cls._original_selections.items():
            field = cls.env[model_name]._fields["bank"]
            field.selection = original["selection"]
            field._selection = original["_selection"]
        super().tearDownClass()

    def create_partner_bank(self, acc_number, partner, bank):
        return self.partner_bank_model.create(
            {"acc_number": acc_number, "partner_id": partner.id, "bank_id": bank.id}
        )

    def action_bank_export_excel(self, bank_payment):
        excel_list = bank_payment.action_export_excel_file()
        self.assertEqual(excel_list["report_type"], "xlsx")

    def create_bank_payment_profile(self, bank, data_dict):
        """This function is common create profile, Format of data_dict is
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
        profile = self.bank_payment_profile_model.create(
            {
                "name": f"Test Profile {bank}",
                "bank": bank,
                "line_ids": [
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
        return profile

    def create_bank_template(self, bank, lines):
        """Create a bank.template with its template_line_ids.

        Each line is a dict of bank.template.line fields, e.g.
        {"sequence": 10, "field_length": 10, "name": "...",
         "source_type": "fixed", "fixed_value": "..."}
        """
        template = self.bank_template_model.create(
            {
                "name": f"Test Template {bank}",
                "bank": bank,
                "template_line_ids": [Command.create(line) for line in lines],
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
