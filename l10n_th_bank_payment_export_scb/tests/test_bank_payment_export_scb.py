# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


@tagged("post_install", "-at_install")
class TestBankPaymentExportSCB(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
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
        # Create bank payment
        cls.bank_payment = cls.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "SICOTHBK",
                "template_id": cls.template1.id,
            }
        )
        cls.bank_payment._onchange_template_id()
        cls.bank_payment.effective_date = cls.today
        cls.bank_payment.action_get_all_payments()

    def test_01_scb_export(self):
        self.assertEqual(len(self.bank_payment.export_line_ids), 2)
        self.assertEqual(self.bank_payment.scb_company_id, "COMPANY01")
        self.assertEqual(self.bank_payment.scb_product_code, "MCL")
        self.assertEqual(self.bank_payment.scb_service_type, "04")

        # Check field default
        self.assertTrue(self.bank_payment.is_required_effective_date)
        self.assertTrue(self.bank_payment.scb_is_editable)

        # Test selected scb_execution_date < today
        with self.assertRaises(UserError):
            self.bank_payment.scb_execution_date = "2000-01-01"

        # Add recipient bank on line
        for line in self.bank_payment.export_line_ids:
            self.assertEqual(line.payment_id.export_status, "to_export")
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id

        self.bank_payment.action_confirm()

        # Export Excel
        xlsx_data = self.action_bank_export_excel(self.bank_payment)
        self.assertEqual(xlsx_data[1], "xlsx")

        # Export Text File
        text_list = self.bank_payment.action_export_text_file()
        self.assertEqual(self.bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = self.bank_payment._export_bank_payment_text_file()
        self.assertNotEqual(
            text_word,
            "Demo Text File. You can inherit function "
            "_generate_bank_payment_text() for customize your format.",
        )

    def test_02_scb_invoice_wht(self):
        # TODO
        pass

    def test_03_scb_mcl(self):
        self.assertEqual(self.bank_payment.scb_product_code, "MCL")
        # Add value test
        self.bank_payment.scb_bank_type = "2"
        self.bank_payment.effective_date = self.today
        self.bank_payment.scb_delivery_mode = "C"
        self.bank_payment.scb_pickup_location = "C001"
        self.bank_payment.scb_is_invoice_present = True

        # Export Text File MCL
        text_list = self.bank_payment.action_export_text_file()
        self.assertEqual(self.bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = self.bank_payment._export_bank_payment_text_file()
        text_split = text_word.split("\r\n")
        # MCL same day should show "2"
        self.assertEqual(text_split[1][102], "2")
        # Delivery Mode C should default from pickup location
        self.assertEqual(text_split[2][65:69], "C001")
        # Show invoice
        invoices = self.bank_payment.export_line_ids[0].payment_id.reconciled_bill_ids
        self.assertEqual(text_split[2][109:115], "000001")
        self.assertEqual(
            text_split[2][115:131], "0000000000%s" % (int(invoices.amount_total * 1000))
        )

    def test_04_scb_bnt(self):
        # Add value test
        self.bank_payment.scb_product_code = "BNT"
        self.bank_payment.effective_date = self.today
        self.bank_payment.scb_service_type_bahtnet = "10"

        # Check constraints
        with self.assertRaises(UserError):
            self.bank_payment.export_line_ids[0].payment_partner_bank_id = False
            self.bank_payment.action_confirm()

        # Check add beneficiary email more than 64 char, it should error
        with self.assertRaises(UserError):
            self.bank_payment.export_line_ids[0].scb_beneficiary_email = "A" * 65
            self.bank_payment.action_confirm()

        self.assertEqual(self.bank_payment.scb_product_code, "BNT")

        # Export Text File BNT
        text_list = self.bank_payment.action_export_text_file()
        self.assertEqual(self.bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = self.bank_payment._export_bank_payment_text_file()
        text_split = text_word.split("\r\n")
        # BNT service type should show "10"
        self.assertEqual(text_split[2][283:285], "10")

    def test_05_scb_mcp(self):
        # Add value test
        self.bank_payment.scb_product_code = "MCP"
        self.bank_payment.effective_date = self.today
        self.bank_payment.scb_pickup_location_cheque = "C002"
        self.bank_payment.scb_delivery_mode = "C"

        # Check constraint MCP can't select scb_delivery_mode = "S"
        with self.assertRaises(UserError):
            with Form(self.bank_payment) as b:
                b.scb_delivery_mode = "S"

        self.assertEqual(len(self.bank_payment.export_line_ids), 2)
        self.assertEqual(self.bank_payment.scb_product_code, "MCP")

        # Export Text File MCP
        text_list = self.bank_payment.action_export_text_file()
        self.assertEqual(self.bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = self.bank_payment._export_bank_payment_text_file()
        text_split = text_word.split("\r\n")
        # MCP receiver bank code should default "014" (SCB)
        self.assertEqual(text_split[2][180:183], "014")

        # MCP receiver bank name should default "SCB" (SCB)
        self.assertIn("SCB", text_split[2][183:218])

        # MCP receiver branch code should default "0111" (SCB)
        self.assertEqual(text_split[2][218:222], "0111")

        # Delivery Mode C should default from pickup location cheque
        self.assertEqual(text_split[2][65:69], "C002")

    def test_06_scb_outward_remittance(self):
        # Add value test
        self.bank_payment.write(
            {
                "scb_outward_remittance": True,
                "scb_rate_type": "SP",
                "scb_charge_flag": "A",
                "effective_date": self.today,
                "scb_objective_code": "318004",
                "scb_document_support": "01",
                "scb_corp_id": "corp12345678",
            }
        )

        self.assertEqual(len(self.bank_payment.export_line_ids), 2)

        # Export Text File Outward Remittance
        text_list = self.bank_payment.action_export_text_file()
        self.assertEqual(self.bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = self.bank_payment._export_bank_payment_text_file()
        # Check corp_id in text file (char 39 - 50)
        self.assertEqual(text_word[38:50], "corp12345678")
