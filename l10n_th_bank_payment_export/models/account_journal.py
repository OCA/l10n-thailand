# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    payment_export_config_ids = fields.One2many(
        comodel_name="bank.payment.config",
        inverse_name="journal_id",
        string="Bank Payment Configuration",
        index=True,
    )
