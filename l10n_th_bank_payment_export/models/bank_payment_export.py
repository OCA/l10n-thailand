# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentExport(models.Model):
    _name = "bank.payment.export"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Bank Payment Export File"
    _check_company_auto = True

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
    template_id = fields.Many2one(
        comodel_name="bank.payment.template",
        string="Template",
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
        check_company=True,
    )
    effective_date = fields.Date(
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    is_required_effective_date = fields.Boolean(
        compute="_compute_required_effective_date",
        default=False,
        copy=False,
    )
    export_line_ids = fields.One2many(
        comodel_name="bank.payment.export.line",
        inverse_name="payment_export_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
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
            ("done", "Exported"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        default="draft",
        tracking=True,
    )

    @api.onchange("template_id")
    def _onchange_template_id(self):
        """Update field following bank payment template"""
        template = self.template_id
        if template:
            self.bank = template.bank
            for line in template.template_config_line:
                self[line.field_id.name] = line.value

    @api.depends("bank")
    def _compute_required_effective_date(self):
        self.is_required_effective_date = False

    @api.depends("export_line_ids", "export_line_ids.state")
    def _compute_total_amount(self):
        for rec in self:
            # Amount total without line rejected
            rec.total_amount = sum(
                rec.export_line_ids.filtered(lambda l: l.state != "reject").mapped(
                    "payment_amount"
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("bank.payment.export") or "/"
                )
        return super().create(vals_list)

    def unlink(self):
        """Check state draft can delete only."""
        if any(rec.state != "draft" for rec in self):
            raise UserError(_("You are trying to delete a record state is not 'draft'"))
        return super().unlink()

    def _domain_payment_id(self):
        """Condition search all payment
        1. Currency same as company currency
        2. Company same as company_id
        3. Payment not exported and state 'posted' only
        4. Payment method must be 'Manual' on Vendor Payment
        5. Journal payment must be type 'Bank' only
        """
        method_manual_out = self.env.ref("account.account_payment_method_manual_out")
        domain = [
            ("export_status", "=", "draft"),
            ("state", "=", "posted"),
            ("payment_method_id", "=", method_manual_out.id),
            ("journal_id.type", "=", "bank"),
            ("company_id", "=", self.company_id.id),
            ("currency_id", "=", self.currency_id.id),
        ]
        return domain

    def action_get_all_payments(self):
        self.ensure_one()
        domain = self._domain_payment_id()
        payments = self.env["account.payment"].search(domain)
        if payments:
            payment_vals = [
                {"payment_export_id": self.id, "payment_id": payment.id}
                for payment in payments
            ]
            # clear old value first
            self.export_line_ids.unlink()
            self.export_line_ids.create(payment_vals)
        return True

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
        self.ensure_one()
        return (
            "Demo Text File. You can inherit function "
            "_generate_bank_payment_text() for customize your format."
        )

    def _export_bank_payment_text_file(self):
        self.ensure_one()
        return self._generate_bank_payment_text()

    def _check_constraint_line(self):
        # Add condition with line on this function
        return

    def _check_constraint_confirm(self):
        # Add condition on this function
        for rec in self:
            if not rec.export_line_ids:
                raise UserError(_("You need to add a line before confirm."))
            rec._check_constraint_line()

    def action_draft(self):
        return self.write({"state": "draft"})

    def action_confirm(self):
        self._check_constraint_confirm()
        self.export_line_ids.mapped("payment_id").write({"export_status": "to_export"})
        return self.write({"state": "confirm"})

    def action_done(self):
        self.export_line_ids.mapped("payment_id").write({"export_status": "exported"})
        return self.write({"state": "done"})

    def action_cancel(self):
        """Reset export_status on payment to 'Draft' and cancel this document"""
        self.export_line_ids.clear_payment_exported()
        return self.write({"state": "cancel"})

    def action_reject(self):
        """Reset export_status on payment to 'Draft' and reject this document"""
        self.export_line_ids.clear_payment_exported()
        return self.write({"state": "reject"})

    def action_export_text_file(self):
        self.ensure_one()
        report = self.print_report("qweb-text")
        self.action_done()
        return report

    def action_export_excel_file(self):
        self.ensure_one()
        return self.print_report("xlsx")

    def _get_context_create_bank_payment_export(self, payments):
        ctx = self.env.context.copy()
        export_lines = [(0, 0, {"payment_id": payment}) for payment in payments.ids]
        payment_bic_bank = list(set(payments.mapped("journal_id.bank_id.bic")))
        payment_bank = len(payment_bic_bank) == 1 and payment_bic_bank[0] or []
        ctx.update(
            {
                "default_template_id": payments[0].bank_payment_template_id.id,
                "default_bank": payment_bank,
                "default_export_line_ids": export_lines,
                "default_currency_id": payments[0].currency_id.id,
            }
        )
        return ctx

    def _get_amount_no_decimal(self, amount, digits=False):
        """Implementation is available"""
        return amount

    @api.constrains("effective_date")
    def check_effective_date(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.effective_date and rec.effective_date < today:
                raise UserError(
                    _("Effective Date must be more than or equal {}").format(
                        today.strftime("%d/%m/%Y")
                    )
                )

    @api.constrains("bank")
    def check_bank_payment(self):
        for rec in self:
            payment_bic_bank = list(
                set(rec.export_line_ids.mapped("payment_journal_id.bank_id.bic"))
            )
            if rec.bank and any(rec.bank != bank for bank in payment_bic_bank):
                raise UserError(
                    _(
                        "You can not selected bank difference with bank journal on payment."
                    )
                )

    def _check_constraint_create_bank_payment_export(self, payments):
        comment_template = payments[0].bank_payment_template_id
        previous_currency = False
        for payment in payments:
            if payment.bank_payment_template_id != comment_template:
                raise UserError(
                    _("All payments must have the same bank payment template.")
                )
            if payment.export_status != "draft":
                raise UserError(_("Payments have been already exported."))
            if payment.state != "posted":
                raise UserError(_("You can export bank payments state 'posted' only"))
            if previous_currency and payment.currency_id != previous_currency:
                raise UserError(_("You can export bank payments with 1 currency only."))
            previous_currency = payment.currency_id

    @api.model
    def action_create_bank_payment_export(self):
        """Create bank payment export from vendor payments"""
        view = self.env.ref("l10n_th_bank_payment_export.bank_payment_export_view_form")
        payments = self.env["account.payment"].browse(
            self.env.context.get("active_ids", [])
        )
        if not payments:
            return
        self._check_constraint_create_bank_payment_export(payments)
        ctx = self._get_context_create_bank_payment_export(payments)
        return {
            "name": _("Bank Payment Export"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "bank.payment.export",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "context": ctx,
        }
