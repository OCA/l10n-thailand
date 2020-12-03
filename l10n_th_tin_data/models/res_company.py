from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tin_check_webservices = fields.Boolean(string="Verify TIN with RD web services")
