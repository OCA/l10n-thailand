# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    check_layout_id = fields.Many2one(
        comodel_name="account.payment.check.report", string="Check format"
    )
    tax_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        string="Tax Report Format",
        required=True,
    )
    wht_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        string="WHT Report Format",
        required=True,
    )
