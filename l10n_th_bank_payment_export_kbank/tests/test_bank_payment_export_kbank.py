# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportKBank(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
