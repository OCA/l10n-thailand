from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tin_check_webservices = fields.Boolean(related='company_id.tin_check_webservices', readonly=False,
        string='Verify TIN with RD web services')
