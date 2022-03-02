# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportKTB(CommonBankPaymentExport):
    def setUp(self):
        super().setUp()
        # setup config
        self.config_ktb_company_id = self.create_bank_payment_config(
            name="KTB Company ID",
            field_name="config_ktb_company_id",
            value="Test KTB Company",
            default=True,
        )
        self.config_ktb_sender_name = self.create_bank_payment_config(
            name="KTB Sender Name",
            field_name="config_ktb_sender_name",
            value="Test KTB Sender Name",
            default=True,
        )

    def test_01_bank_payment_config(self):
        """ Test default bank payment config """
        self.config_ktb_sender_name.is_default = False
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "KRTHTHBK",
            }
        )
        self.assertEqual(bank_payment.config_ktb_company_id, self.config_ktb_company_id)
        self.assertFalse(bank_payment.config_ktb_sender_name)
        # Test change it to default
        self.config_ktb_sender_name.is_default = True
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "KRTHTHBK",
            }
        )
        self.assertEqual(
            bank_payment.config_ktb_sender_name, self.config_ktb_sender_name
        )

        # Can't create config default with field duplicate
        with self.assertRaises(UserError):
            self.create_bank_payment_config(
                name="KTB Company ID2",
                field_name="config_ktb_company_id",
                value="Test KTB Company2",
                default=True,
            )

    def test_02_ktb_export(self):
        bank_payment = self.bank_payment_export_model.create(
            {
                "name": "/",
                "bank": "KRTHTHBK",
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
        # Criteria bank KTB is not selected
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        # Test onchange and effective date < today
        with self.assertRaises(UserError):
            with Form(bank_payment) as bp:
                bp.ktb_bank_type = "standard"
                bp.ktb_service_type_standard = "04"
                bp.effective_date = fields.Date.today() - timedelta(days=3)
        with Form(bank_payment) as bp:
            bp.ktb_bank_type = "direct"
            bp.ktb_service_type_direct = "14"
            bp.effective_date = fields.Date.today()
        self.assertFalse(bank_payment.ktb_service_type_standard)
        self.assertTrue(bank_payment.ktb_service_type_direct)
        # Type direct can't export payment to other bank
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        with Form(bank_payment) as bp:
            bp.ktb_bank_type = "standard"
            bp.ktb_service_type_standard = "04"
        # Type standard can't export payment to the same bank
        origin = []
        for line in bank_payment.export_line_ids:
            origin.append(line.payment_partner_bank_id.bank_id.bic)
            line.payment_partner_bank_id.bank_id.bic = bank_payment.bank
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        for i, line in enumerate(bank_payment.export_line_ids):
            line.payment_partner_bank_id.bank_id.bic = origin[i]
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
