# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestWHTCertForm(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.wht_cert = cls.env["withholding.tax.cert"]
        cls.withholdin_tax_cert_form = cls.env.ref(
            "l10n_th_account_wht_cert_form.withholding_tax_pdf_report"
        )

    def _create_direct_wht_cert(self):
        wht_cert = self.wht_cert.create(
            {
                "partner_id": self.partner_1.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "wht_line": [
                    (
                        0,
                        0,
                        {
                            "wht_cert_income_type": "6",
                            "wht_cert_income_desc": "Other Text",
                            "amount": 10.0,
                            "wht_percent": 1.0,
                            "base": 1000.0,
                        },
                    )
                ],
            }
        )
        return wht_cert

    def test_01_print_wht_cert_form(self):
        wht_cert = self._create_direct_wht_cert()
        content = self.withholdin_tax_cert_form._render_qweb_pdf(
            self.withholdin_tax_cert_form.report_name, [wht_cert.id]
        )
        self.assertEqual(content[1], "html")
        # check report name pdf
        # display name is False because create wht direct.
        self.assertEqual(
            wht_cert._get_report_base_filename(), "WHT Certificates - False"
        )
