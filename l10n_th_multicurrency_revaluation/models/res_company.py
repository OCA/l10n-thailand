# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    revaluation_loss_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Revaluation loss account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    revaluation_gain_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Revaluation gain account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    revaluation_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Revaluation Analytic account",
        domain=lambda self: [("company_id", "=", self.env.company.id)],
    )
    provision_bs_loss_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Provision B.S. loss account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    provision_bs_gain_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Provision B.S. gain account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    provision_pl_loss_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Provision P&L loss account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    provision_pl_gain_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Provision P&L gain account",
        domain=lambda self: [
            ("company_id", "=", self.env.company.id),
            ("internal_type", "=", "other"),
            ("deprecated", "=", False),
        ],
    )
    provision_pl_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Provision P&L Analytic account"
    )
    currency_reval_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Currency gain & loss Default Journal",
        domain=[("type", "=", "general")],
    )
    auto_post_entries = fields.Boolean(
        string="Auto Post Created Entries",
        help="If marked, the entries created in the process will be"
        " posted automatically.",
        default=True,
        readonly=False,
    )
