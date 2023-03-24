# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportBBL(CommonBankPaymentExport):
    def setUp(self):
        super().setUp()
        # setup config
        self.config_bbl_company_code = self.create_bank_payment_config(
            name="BBL Company ID",
            field_name="config_bbl_company_code",
            value="Test BBL Company",
            bank="BKKBTHBK",
            default=True,
        )
        self.config_bbl_customer_batch_smart = self.create_bank_payment_config(
            name="BBL Smart Batch Ref",
            field_name="config_bbl_customer_batch_smart",
            value="Test BBL Smart Batch Ref",
            bank="BKKBTHBK",
            default=True,
        )
        self.config_bbl_customer_batch_direct = self.create_bank_payment_config(
            name="BBL Direct Batch Ref",
            field_name="config_bbl_customer_batch_direct",
            value="Test BBL Direct Batch Ref",
            bank="BKKBTHBK",
            default=True,
        )

    def test_01_bank_payment_config(self):
        """Test default bank payment config"""
        self.config_bbl_company_code.is_default = False
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "BKKBTHBK",
            }
        )
        self.assertFalse(bank_payment.config_bbl_company_code)
        self.assertEqual(
            bank_payment.config_bbl_customer_batch_direct,
            self.config_bbl_customer_batch_direct,
        )
        self.assertEqual(
            bank_payment.config_bbl_customer_batch_smart,
            self.config_bbl_customer_batch_smart,
        )
        # Test change it to default
        self.config_bbl_company_code.is_default = True
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "BKKBTHBK",
            }
        )
        self.assertEqual(
            bank_payment.config_bbl_company_code, self.config_bbl_company_code
        )

        # Can't create config default with field duplicate
        with self.assertRaises(UserError):
            self.create_bank_payment_config(
                name="BBL Company ID 2",
                field_name="config_bbl_company_code",
                value="Test BBL Company 2",
                bank="BKKBTHBK",
                default=True,
            )

    def test_02_bbl_export(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "BKKBTHBK",
            }
        )
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
        with Form(bank_payment) as bp:
            bp.bbl_product_code = "DCB01"
            bp.bbl_company_bank_account = self.env.company.partner_id.bank_ids[0]
            bp.bbl_bot_type = "04"
            bp.bbl_payee_charge = "BEN"
        self.assertTrue(bank_payment.bbl_bank_type)
        self.assertEqual(bank_payment.bbl_bank_type, "direct")
        # Type direct can't export payment to other bank
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        with Form(bank_payment) as bp:
            bp.bbl_product_code = "SMC04"
        self.assertEqual(bank_payment.bbl_bank_type, "smart")
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