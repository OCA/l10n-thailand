# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


@tagged("post_install", "-at_install")
class TestBankPaymentExportSCB(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Search field default
        field_scb_company_id = cls.field_model.search(
            [("name", "=", "scb_company_id"), ("model", "=", "bank.payment.export")]
        )
        field_scb_product_code = cls.field_model.search(
            [("name", "=", "scb_product_code"), ("model", "=", "bank.payment.export")]
        )
        field_scb_service_type = cls.field_model.search(
            [("name", "=", "scb_service_type"), ("model", "=", "bank.payment.export")]
        )
        # setup template
        data_dict = [
            {
                "field_id": field_scb_company_id.id,
                "value": "COMPANY01",
            },
            {
                "field_id": field_scb_product_code.id,
                "value": "MCL",
            },
            {
                "field_id": field_scb_service_type.id,
                "value": "04",
            },
        ]
        cls.template1 = cls.create_bank_payment_template(
            cls,
            "SICOTHBK",
            data_dict,
        )

        cls.today = fields.Date.today()

    def test_01_bank_payment_template(self):
        """Test default bank payment template"""
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "SICOTHBK",
                "template_id": self.template1.id,
            }
        )
        self.assertFalse(bank_payment.scb_company_id)
        self.assertFalse(bank_payment.scb_product_code)
        self.assertFalse(bank_payment.scb_service_type)
        # Add template in bank payment export, it should default
        bank_payment._onchange_template_id()
        self.assertEqual(bank_payment.scb_company_id, "COMPANY01")
        self.assertEqual(bank_payment.scb_product_code, "MCL")
        self.assertEqual(bank_payment.scb_service_type, "04")

    def test_02_scb_export(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "SICOTHBK",
                "template_id": self.template1.id,
            }
        )
        bank_payment._onchange_template_id()
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 2)
        # Add recipient bank on line
        for line in bank_payment.export_line_ids:
            self.assertEqual(line.payment_id.export_status, "to_export")
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id

        # Check field default
        self.assertTrue(bank_payment.is_required_effective_date)
        self.assertTrue(bank_payment.scb_is_editable)
        # Test selected scb_execution_date < today
        bank_payment.effective_date = self.today
        with self.assertRaises(UserError):
            bank_payment.scb_execution_date = "2000-01-01"
        bank_payment.action_confirm()

        # Export Excel
        xlsx_data = self.action_bank_export_excel(bank_payment)
        self.assertEqual(xlsx_data[1], "xlsx")

        # Export Text File
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = bank_payment._export_bank_payment_text_file()
        self.assertNotEqual(
            text_word,
            "Demo Text File. You can inherit function "
            "_generate_bank_payment_text() for customize your format.",
        )
        self.assertEqual(bank_payment.state, "done")

    def test_03_scb_mcl(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "SICOTHBK",
                "template_id": self.template1.id,
            }
        )
        bank_payment._onchange_template_id()
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 2)
        self.assertEqual(bank_payment.scb_product_code, "MCL")
        # Add value test
        bank_payment.scb_bank_type = "2"
        bank_payment.effective_date = self.today
        bank_payment.scb_delivery_mode = "C"
        bank_payment.scb_pickup_location = "C001"
        bank_payment.scb_is_invoice_present = True

        # Export Text File MCL
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = bank_payment._export_bank_payment_text_file()
        text_split = text_word.split("\r\n")
        # MCL same day should show "2"
        self.assertEqual(text_split[1][102], "2")
        # Delivery Mode C should default from pickup location
        self.assertEqual(text_split[2][65:69], "C001")
        # Show invoice
        invoices = bank_payment.export_line_ids[0].payment_id.reconciled_bill_ids
        self.assertEqual(text_split[2][109:115], "000001")
        self.assertEqual(
            text_split[2][115:131], "0000000000%s" % (int(invoices.amount_total * 1000))
        )

        self.assertEqual(bank_payment.state, "done")

    def test_04_scb_bnt(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "SICOTHBK",
                "template_id": self.template1.id,
            }
        )
        bank_payment._onchange_template_id()
        bank_payment.action_get_all_payments()
        bank_payment.scb_product_code = "BNT"
        self.assertEqual(len(bank_payment.export_line_ids), 2)
        self.assertEqual(bank_payment.scb_product_code, "BNT")
        # Add value test
        bank_payment.effective_date = self.today

        # Export Text File BNT
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        bank_payment._export_bank_payment_text_file()
        self.assertEqual(bank_payment.state, "done")
