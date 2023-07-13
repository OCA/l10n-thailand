# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    revaluation_loss_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Revaluation loss account",
        domain=[("internal_type", "=", "other")],
    )
    revaluation_gain_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Revaluation gain account",
        domain=[("internal_type", "=", "other")],
    )
    revaluation_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Revaluation Analytic account"
    )
    currency_reval_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Currency gain & loss Default Journal",
        domain=[("type", "=", "general")],
    )
    reversable_revaluations = fields.Boolean(
        help="Revaluations entries will be created " 'as "To Be Reversed".',
        default=True,
    )
    auto_post_entries = fields.Boolean(
        string="Auto Post Created Entries",
        help="If marked, the entries created in the process will be"
        "posted automatically.",
        default=True,
        readonly=False,
    )
