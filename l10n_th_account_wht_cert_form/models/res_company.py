# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    wht_form_preprint = fields.Boolean(
        string="Preprint - Withholding Tax Cert Form",
        help="If checked, wht cert form will show layout pre-print",
    )
