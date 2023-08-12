# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankPaymentExportTester(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("TEST", "Test Bank")],
        ondelete={"TEST": "cascade"},
    )


class BankPaymentTemplateTester(models.Model):
    _inherit = "bank.payment.template"

    bank = fields.Selection(
        selection_add=[("TEST", "Test Bank")],
        ondelete={"TEST": "cascade"},
    )
