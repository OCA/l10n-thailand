# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentExport(models.Model):
    _name = "bank.payment.export"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Bank Payment Export File"

    name = fields.Char(
        default="/",
        index=True,
        copy=False,
        required=True,
        readonly=True,
    )
    bank = fields.Selection(
        selection=[],
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    export_line_ids = fields.One2many(
        comodel_name="bank.payment.export.line",
        inverse_name="payment_export_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    total_amount = fields.Monetary(
        compute="_compute_total_amount",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        default="draft",
        tracking=True,
    )

    @api.depends("export_line_ids", "export_line_ids.state")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(
                rec.export_line_ids.filtered(lambda l: l.state != "cancel").mapped(
                    "payment_amount"
                )
            )

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("bank.payment.export") or "/"
            )
        return super().create(vals)

    def unlink(self):
        """Check state draft can delete only."""
        if any(rec.state != "draft" for rec in self):
            raise UserError(_("You are trying to delete a record state is not 'draft'"))
        return super().unlink()

    def _domain_payment_id(self):
        """Condition search all payment
        1. Currency same as company currency
        2. Payment not exported and state 'posted' only
        3. Payment method must be 'Manual' on Vendor Payment
        4. Journal payment must be type 'Bank' only
        """
        method_manual_out = self.env.ref("account.account_payment_method_manual_out")
        domain = [
            ("is_export", "=", False),
            ("state", "=", "posted"),
            ("payment_method_id", "=", method_manual_out.id),
            ("currency_id", "=", self.env.company.currency_id.id),
            ("journal_id.type", "=", "bank"),
        ]
        return domain

    def action_get_all_payments(self):
        self.ensure_one()
        domain = self._domain_payment_id()
        payments = self.env["account.payment"].search(domain)
        payment_vals = [
            {"payment_export_id": self.id, "payment_id": payment.id}
            for payment in payments
        ]
        # clear old value first
        self.export_line_ids.unlink()
        self.export_line_ids.create(payment_vals)
        return

    def _get_report_base_filename(self):
        self.ensure_one()
        return "{}".format(self.name)

    def _get_view_report_text(self):
        return "l10n_th_bank_payment_export.action_payment_demo_txt"

    def _get_view_report_xlsx(self):
        return "l10n_th_bank_payment_export.action_export_payment_xlsx"

    def print_report(self, report_type):
        self.ensure_one()
        view_report = ""
        if report_type == "qweb-text":
            view_report = self._get_view_report_text()
        elif report_type == "xlsx":
            view_report = self._get_view_report_xlsx()
        return self.env.ref(view_report).sudo().report_action(self, config=False)

    def _generate_bank_payment_text(self):
        return

    def _export_bank_payment_text_file(self):
        self.ensure_one()
        if self.bank:
            return self._generate_bank_payment_text()
        return (
            "Demo Text File. You can inherit function "
            "_generate_bank_payment_text() for customize your format."
        )

    def _check_constraint_confirm(self):
        # Add condition here
        for rec in self:
            if not rec.export_line_ids:
                raise UserError(_("You need to add a line before confirm."))
            if any(rec.export_line_ids.mapped("payment_id.is_export")):
                raise UserError(_("Another document was used to export the payment."))
            if any(not line.payment_partner_bank_id for line in rec.export_line_ids):
                raise UserError(_("Recipient Bank is not selected."))

    def action_draft(self):
        self.export_line_ids.clear_payment_exported()
        return self.write({"state": "draft"})

    def action_confirm(self):
        self._check_constraint_confirm()
        self.export_line_ids.mapped("payment_id").write({"is_export": True})
        return self.write({"state": "confirm"})

    def action_done(self):
        return self.write({"state": "done"})

    def action_cancel(self):
        """Normally, you can create document bank export payment
        and select duplicate payment (state draft only).
        Example:
            document A (state draft) > payment A
            document B (state draft) > payment A
            -------
            document A (state confirm) > payment A
            document B (state draft) > payment A ==> can't confirm, must cancel
            -------
            document A (state confirm) > payment A
            document B (state cancel) > payment A ==> exported should be True
            -------
            document A (state cancel) > payment A ==> exported should be False
            document B (state cancel) > payment A
        """
        if self.state != "draft":
            self.export_line_ids.clear_payment_exported()
        return self.write({"state": "cancel"})

    def action_export_text_file(self):
        self.ensure_one()
        report = self.print_report("qweb-text")
        self.action_done()
        return report

    def action_export_excel_file(self):
        self.ensure_one()
        return self.print_report("xlsx")

    def _get_context_create_bank_payment_export(self):
        ctx = self.env.context.copy()
        active_ids = self.env.context.get("active_ids", [])
        export_lines = [(0, 0, {"payment_id": x}) for x in active_ids]
        ctx.update({"default_export_line_ids": export_lines})
        return ctx

    def _check_constraint_create_bank_payment_export(self, payments):
        method_manual_out = self.env.ref("account.account_payment_method_manual_out")
        for payment in payments:
            if (
                payment.payment_method_id.id != method_manual_out.id
                or payment.journal_id.type != "bank"
            ):
                raise UserError(
                    _(
                        "You can export bank payments with journal 'Bank' "
                        "and Payment method 'Manual' only"
                    )
                )
            if payment.is_export:
                raise UserError(_("Payments have been already exported."))
            if payment.state != "posted":
                raise UserError(_("You can export bank payments state 'posted' only"))
            if payment.company_id.currency_id != payment.currency_id:
                raise UserError(
                    _(
                        "Payments must be currency '{}' only".format(
                            payment.company_id.currency_id.name
                        )
                    )
                )

    @api.model
    def action_create_bank_payment_export(self):
        """ Create bank payment export from vendor payments """
        view = self.env.ref("l10n_th_bank_payment_export.bank_payment_export_view_form")
        payments = self.env["account.payment"].browse(
            self.env.context.get("active_ids", [])
        )
        self._check_constraint_create_bank_payment_export(payments)
        ctx = self._get_context_create_bank_payment_export()
        return {
            "name": _("Bank Payment Export"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "bank.payment.export",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "context": ctx,
        }
