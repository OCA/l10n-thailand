# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch = fields.Char(
        string='Branch',
        size=5,
        help="Branch ID, e.g., 0000, 0001, ..."
    )
