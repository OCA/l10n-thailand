# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    module_payment_register_perm_inbound = fields.Boolean(
        string="Use Persistent Document on Inbound Payment",
    )
    module_payment_register_perm_outbound = fields.Boolean(
        string="Use Persistent Document on Outbound Payment",
    )
