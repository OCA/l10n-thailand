# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestWHTCertForm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create({"name": "Test Partner"})
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
                    Command.create(
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

    def _create_multi_type_wht_cert(self):
        """A cert whose lines span two income types, one of them twice."""
        return self.wht_cert.create(
            {
                "partner_id": self.partner_1.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "wht_line": [
                    Command.create(
                        {
                            "wht_cert_income_type": "1",
                            "wht_cert_income_desc": "Salary A",
                            "base": 1000.0,
                            "amount": 10.0,
                            "wht_percent": 1.0,
                        },
                    ),
                    Command.create(
                        {
                            "wht_cert_income_type": "1",
                            "wht_cert_income_desc": "Salary B",
                            "base": 2000.0,
                            "amount": 20.0,
                            "wht_percent": 1.0,
                        },
                    ),
                    Command.create(
                        {
                            "wht_cert_income_type": "2",
                            "wht_cert_income_desc": "Service fee",
                            "base": 500.0,
                            "amount": 5.0,
                            "wht_percent": 1.0,
                        },
                    ),
                ],
            }
        )

    def test_02_group_wht_line_sums_by_income_type(self):
        """_group_wht_line groups lines and sums base/amount per income type.

        The report reads the result as dicts and compares
        wht_cert_income_type against string literals ("1", "2", ...), so the
        key has to stay a plain string and the totals have to be summed.
        """
        wht_cert = self._create_multi_type_wht_cert()
        groups = wht_cert._group_wht_line(wht_cert.wht_line)
        by_type = {group["wht_cert_income_type"]: group for group in groups}
        self.assertEqual(sorted(by_type), ["1", "2"])
        # the two type "1" lines are summed together
        self.assertEqual(by_type["1"]["base"], 3000.0)
        self.assertEqual(by_type["1"]["amount"], 30.0)
        # type "2" keeps its own totals
        self.assertEqual(by_type["2"]["base"], 500.0)
        self.assertEqual(by_type["2"]["amount"], 5.0)
        # a Selection groupby must come back as the raw string, not a recordset
        for key in by_type:
            self.assertIsInstance(key, str)

    def test_03_report_prints_grouped_totals(self):
        """The grouped totals reach the rendered certificate."""
        wht_cert = self._create_multi_type_wht_cert()
        content, content_type = self.withholdin_tax_cert_form._render_qweb_pdf(
            self.withholdin_tax_cert_form.report_name, [wht_cert.id]
        )
        self.assertEqual(content_type, "html")
        body = content.decode() if isinstance(content, bytes) else content
        # summed type "1" total, formatted by the template as '{0:,.2f}'
        self.assertIn("3,000.00", body)
        self.assertIn("30.00", body)
        # type "2" total kept separate
        self.assertIn("500.00", body)
