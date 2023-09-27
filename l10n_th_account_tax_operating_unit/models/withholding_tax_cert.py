# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        compute="_compute_operating_unit_id",
        store=True,
        readonly=False,
        tracking=True,
    )

    @api.depends("payment_id", "payment_id.operating_unit_id", "move_id", "move_id.operating_unit_id")
    def _compute_operating_unit_id(self):
        default_ou = self.env["res.users"].operating_unit_default_get(self.env.uid)
        for rec in self:
            ou = default_ou
            if rec.payment_id:
                if rec.payment_id.operating_unit_id:
                    ou = rec.payment_id.operating_unit_id
                else:
                    moves = (
                        rec.payment_id.reconciled_bill_ids
                        or rec.payment_id.reconciled_invoice_ids
                    )
                    ous = moves.mapped("operating_unit_id")
                    if len(ous) == 1:
                        ou = ous
            elif rec.move_id and rec.move_id.operating_unit_id:
                ou = rec.move_id.operating_unit_id
            rec.operating_unit_id = ou
