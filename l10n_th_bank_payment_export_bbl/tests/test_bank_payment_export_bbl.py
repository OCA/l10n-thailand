# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportBBL(CommonBankPaymentExport):
    def setUp(self):
        super().setUp()
        # paremeter config
        self.company_code = self.env.ref(
            "l10n_th_bank_payment_export_bbl.export_payment_bbl_company_code"
        )
        self.smart_customer_ref = self.env.ref(
            "l10n_th_bank_payment_export_bbl.export_payment_bbl_smart_customer_batch_ref"
        )
        self.direct_customer_ref = self.env.ref(
            "l10n_th_bank_payment_export_bbl.export_payment_bbl_direct_customer_batch_ref"
        )

    def test_01_config_parameter(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "BKKBTHBK",
            }
        )
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 2)
        # check config parameter
        self.assertFalse(bank_payment.config_bbl_company_code)
        self.assertFalse(bank_payment.config_bbl_customer_batch_smart)
        self.assertFalse(bank_payment.config_bbl_customer_batch_direct)
        self.company_code.value = "Test Company Code"
        self.smart_customer_ref.value = "Test Smart Ref"
        self.direct_customer_ref.value = "Test Direct Ref"
        bank_payment._compute_bbl_system_parameter()
        self.assertTrue(bank_payment.config_bbl_company_code)
        self.assertTrue(bank_payment.config_bbl_customer_batch_smart)
        self.assertTrue(bank_payment.config_bbl_customer_batch_direct)

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
            self.assertFalse(line.payment_id.is_export)
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
