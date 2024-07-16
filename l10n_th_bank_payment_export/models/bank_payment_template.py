# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankPaymentTemplate(models.Model):
    _name = "bank.payment.template"
    _description = "Template of Bank Payment Configuration"
    _check_company_auto = True

    name = fields.Char(required=True)
    bank = fields.Selection(
        selection=[],
        required=True,
    )
    template_config_line = fields.One2many(
        comodel_name="bank.payment.config",
        inverse_name="template_id",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )


class BankPaymentConfig(models.Model):
    _name = "bank.payment.config"
    _description = "Bank Payment Configuration"

    template_id = fields.Many2one(comodel_name="bank.payment.template", index=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        required=True,
        index=True,
        domain=[("model", "=", "bank.payment.export")],
        ondelete="cascade",
    )
    value = fields.Char(required=True)
