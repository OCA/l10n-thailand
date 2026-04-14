# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.float_utils import float_round


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_create_invoice(self):
        line_qty_before = {
            line.id: line.qty_invoiced for line in self.mapped("order_line")
        }
        existing_move_ids = set(self.mapped("invoice_ids").ids)
        result = super().action_create_invoice()
        new_moves = self.mapped("invoice_ids").filtered(
            lambda m: m.id not in existing_move_ids
        )
        if new_moves:
            self._sync_tax_invoices_from_pickings(new_moves, line_qty_before)
        return result

    def _get_picking_groups_for_bill(self, move, line_qty_before):
        """Return picking-group data covering only the quantities billed in move."""
        po_lines = move.invoice_line_ids.mapped("purchase_line_id").filtered("id")
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
        for inv_line in move.invoice_line_ids:
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

    def _sync_tax_invoices_from_pickings(self, moves, line_qty_before):
        """After creating bills, update or split account.move.tax.invoice records
        based on the tax_invoice_number/date from the stock pickings that cover
        the quantities in each bill.
        """
        taxinvoice_dict = []
        for move in moves:
            groups = self._get_picking_groups_for_bill(move, line_qty_before)
            if not groups:
                continue

            group_list = list(groups.values())
            tax_invoice_ids = move.tax_invoice_ids

            if len(group_list) == 1:
                group = group_list[0]
                if group["tax_invoice_number"] or group["tax_invoice_date"]:
                    tax_invoice_ids.write(
                        {
                            "tax_invoice_number": group["tax_invoice_number"],
                            "tax_invoice_date": group["tax_invoice_date"],
                        }
                    )
                continue

            # Multiple groups - split proportionally with correct rounding.
            # The last group absorbs any remainder so amounts sum exactly to
            # the original values.
            total_amount = sum(g["amount"] for g in group_list)
            if not total_amount:
                continue

            rounding = move.company_currency_id.rounding
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
                        base = float_round(
                            orig_base * ratio, precision_rounding=rounding
                        )
                        balance = float_round(
                            orig_balance * ratio, precision_rounding=rounding
                        )
                        remaining_base -= base
                        remaining_balance -= balance

                    taxinvoice_dict.append(
                        {
                            "move_id": move.id,
                            "move_line_id": tax_inv.move_line_id.id,
                            "partner_id": tax_inv.partner_id.id,
                            "is_stock_split": True,
                            "tax_invoice_number": group["tax_invoice_number"],
                            "tax_invoice_date": group["tax_invoice_date"],
                            "tax_base_amount": base,
                            "balance": balance,
                        }
                    )
        if taxinvoice_dict:
            self.env["account.move.tax.invoice"].create(taxinvoice_dict)
