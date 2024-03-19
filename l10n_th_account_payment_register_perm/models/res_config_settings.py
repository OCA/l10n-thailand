# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_payment_register_perm_inbound = fields.Boolean(
        string="Use Persistent Document on Inbound Payment",
        related="company_id.module_payment_register_perm_inbound",
        readonly=False,
    )
    module_payment_register_perm_outbound = fields.Boolean(
        string="Use Persistent Document on Outbound Payment",
        related="company_id.module_payment_register_perm_outbound",
        readonly=False,
    )
