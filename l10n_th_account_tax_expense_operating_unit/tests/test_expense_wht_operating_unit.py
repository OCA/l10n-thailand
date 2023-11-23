# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_th_account_tax_expense.tests.test_expense_withholding_tax import (
    TestHrExpenseWithholdingTax,
)


@tagged("post_install", "-at_install")
class TestHrExpenseWHTOperatingUnit(TestHrExpenseWithholdingTax):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
