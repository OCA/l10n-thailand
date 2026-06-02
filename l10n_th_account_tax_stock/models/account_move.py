# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.tools.float_utils import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._sync_stock_tax_invoices()
        return moves

    def write(self, vals):
        res = super().write(vals)
        self._sync_stock_tax_invoices()
        return res

    def _sync_stock_tax_invoices(self):
        """Fill tax_invoice_number/date on vendor bills from the stock pickings
        that cover the billed quantities.
        """
        taxinvoice_dict = []
        for move in self:
            # Vendor refunds keep the prior behaviour
            if move.move_type != "in_invoice" or move.state != "draft":
                continue

            pending = move.tax_invoice_ids.filtered(
                lambda t: not t.is_stock_split
                and (not t.tax_invoice_number or t.tax_invoice_number == "/")
            )
            if not pending:
                continue

            line_qty_before = move._stock_line_qty_before()
            groups = move._get_picking_groups_for_bill(line_qty_before)
            if not groups:
                continue

            taxinvoice_dict += move._apply_picking_groups(groups)

        if taxinvoice_dict:
            self.env["account.move.tax.invoice"].create(taxinvoice_dict)

    def _stock_line_qty_before(self):
        """Quantity already invoiced per PO line, excluding this move's lines."""
        self.ensure_one()
        result = {}
        for inv_line in self.invoice_line_ids:
            po_line = inv_line.purchase_line_id
            if not po_line:
                continue
            result.setdefault(po_line.id, po_line.qty_invoiced)
            result[po_line.id] -= inv_line.quantity
        return result

    def _get_picking_groups_for_bill(self, line_qty_before):
        """Return picking-group data covering only the quantities billed."""
        self.ensure_one()
        po_lines = self.invoice_line_ids.mapped("purchase_line_id").filtered("id")
        if not po_lines:
            return {}

        # Prefetch all relevant done moves in one query, then index by PO line id.
        all_done_moves = po_lines.mapped("move_ids").filtered(
            lambda m: m.state == "done" and m.picking_id
        )
        moves_by_line = {}
        for sm in all_done_moves:
            line_id = sm.purchase_line_id.id
            moves_by_line.setdefault(line_id, [])
            moves_by_line[line_id].append(sm)
        # Sort each group once (by date ascending)
        for line_id in moves_by_line:
            moves_by_line[line_id].sort(key=lambda m: m.date)

        groups = {}
        for inv_line in self.invoice_line_ids:
            po_line = inv_line.purchase_line_id
            if not po_line:
                continue

            bill_qty = inv_line.quantity
            invoiced_before = line_qty_before.get(po_line.id, 0.0)
            bill_end = invoiced_before + bill_qty

            cumulative = 0.0
            for sm in moves_by_line.get(po_line.id, []):
                sm_qty = sm.quantity
                overlap_start = max(cumulative, invoiced_before)
                overlap_end = min(cumulative + sm_qty, bill_end)
                effective_qty = max(0.0, overlap_end - overlap_start)

                if effective_qty > 0.0:
                    picking = sm.picking_id
                    key = (
                        picking.tax_invoice_number,
                        picking.tax_invoice_date,
                    )
                    if key not in groups:
                        groups[key] = {
                            "tax_invoice_number": picking.tax_invoice_number,
                            "tax_invoice_date": picking.tax_invoice_date,
                            "amount": 0.0,
                        }
                    groups[key]["amount"] += effective_qty * po_line.price_unit

                cumulative += sm_qty
                if cumulative >= bill_end:
                    break

        return groups

    def _apply_picking_groups(self, groups):
        """Update/split this move's tax invoices from picking groups"""
        self.ensure_one()
        taxinvoice_dict = []
        group_list = list(groups.values())
        tax_invoice_ids = self.tax_invoice_ids

        if len(group_list) == 1:
            group = group_list[0]
            if group["tax_invoice_number"] or group["tax_invoice_date"]:
                tax_invoice_ids.write(
                    {
                        "tax_invoice_number": group["tax_invoice_number"],
                        "tax_invoice_date": group["tax_invoice_date"],
                    }
                )
            return taxinvoice_dict

        # Multiple groups - split proportionally with correct rounding.
        # The last group absorbs any remainder so amounts sum exactly to
        # the original values.
        total_amount = sum(g["amount"] for g in group_list)
        if not total_amount:
            return taxinvoice_dict

        rounding = self.company_currency_id.rounding
        first_group, *rest_groups = group_list

        for tax_inv in tax_invoice_ids:
            orig_base = tax_inv.tax_base_amount
            orig_balance = tax_inv.balance
            remaining_base = orig_base
            remaining_balance = orig_balance

            # Update the original record in-place for the first group
            first_ratio = first_group["amount"] / total_amount
            first_base = float_round(
                orig_base * first_ratio, precision_rounding=rounding
            )
            first_balance = float_round(
                orig_balance * first_ratio, precision_rounding=rounding
            )
            remaining_base -= first_base
            remaining_balance -= first_balance
            tax_inv.write(
                {
                    "is_stock_split": True,
                    "tax_invoice_number": first_group["tax_invoice_number"],
                    "tax_invoice_date": first_group["tax_invoice_date"],
                    "tax_base_amount": first_base,
                    "balance": first_balance,
                }
            )

            # Create one record per remaining group.
            # Including tax_base_amount/balance in create() is safe because
            # _compute_tax_amount skips is_stock_split=True records, so the
            # provided values are never overridden by the compute.
            for group in rest_groups:
                is_last = group is rest_groups[-1]
                if is_last:
                    base = remaining_base
                    balance = remaining_balance
                else:
                    ratio = group["amount"] / total_amount
                    base = float_round(orig_base * ratio, precision_rounding=rounding)
                    balance = float_round(
                        orig_balance * ratio, precision_rounding=rounding
                    )
                    remaining_base -= base
                    remaining_balance -= balance

                taxinvoice_dict.append(
                    {
                        "move_id": self.id,
                        "move_line_id": tax_inv.move_line_id.id,
                        "partner_id": tax_inv.partner_id.id,
                        "is_stock_split": True,
                        "tax_invoice_number": group["tax_invoice_number"],
                        "tax_invoice_date": group["tax_invoice_date"],
                        "tax_base_amount": base,
                        "balance": balance,
                    }
                )
        return taxinvoice_dict
