# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestWTCertForm(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.wt_cert = cls.env["withholding.tax.cert"]
        cls.withholdin_tax_cert_form = cls.env.ref(
            "l10n_th_withholding_tax_cert_form.withholding_tax_pdf_report"
        )

    def _create_direct_wt_cert(self):
        wt_cert = self.wt_cert.create(
            {
                "supplier_partner_id": self.partner_1.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "wt_line": [
                    (
                        0,
                        0,
                        {
                            "wt_cert_income_type": "6",
                            "wt_cert_income_desc": "Other Text",
                            "amount": 10.0,
                            "wt_percent": 1.0,
                            "base": 1000.0,
                        },
                    )
                ],
            }
        )
        return wt_cert

    def test_01_print_wt_cert_form(self):
        wt_cert = self._create_direct_wt_cert()
        self.withholdin_tax_cert_form.render_qweb_pdf(wt_cert.id)
