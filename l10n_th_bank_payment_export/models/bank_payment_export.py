# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


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
    bank_export_format_id = fields.Many2one(
        comodel_name="bank.export.format",
        string="Bank Export Format",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('bank', '=', bank)]",
        tracking=True,
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
                field = line.field_id
                value = line.value
                if field.ttype in ["many2one", "many2many"]:
                    # If value is digit, search by id, else search by name
                    if line.value.isdigit():
                        value = self.env[field.relation].browse(int(line.value)).id
                    else:
                        value = (
                            self.env[field.relation]
                            .search([("name", "=", line.value)], limit=1)
                            .id
                        )
                self[field.name] = value

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
        return "l10n_th_bank_payment_export.action_payment_txt"

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

    def _set_global_dict(self):
        """Set global dict for eval"""
        today = fields.Date.context_today(self)
        today_datetime = fields.Datetime.context_timestamp(
            self.env.user, datetime.now()
        )
        globals_dict = {
            "rec": self,
            "line": self.export_line_ids,
            "today": today,
            "today_datetime": today_datetime,
            "wht_cert": False,
            "invoices": self.env["account.move"],
        }
        return globals_dict

    def _update_global_dict(self, globals_dict, **kwargs):
        """Update global dict with kwargs"""
        globals_dict.update(kwargs)
        return globals_dict

    def _generate_bank_payment_text(self):
        self.ensure_one()
        globals_dict = self._set_global_dict()
        text_parts = []
        processed_match = set()

        # Get format from bank
        if not self.bank_export_format_id:
            raise UserError(_("Bank format not found."))

        exp_format_lines = self.bank_export_format_id.export_format_ids

        for idx, exp_format in enumerate(exp_format_lines):
            if exp_format.display_type:
                continue

            # Skip if value has already been processed, and need_loop is True
            if exp_format.need_loop and exp_format.match_group in processed_match:
                continue

            # Add idx to globals_dict
            globals_dict = self._update_global_dict(globals_dict, idx=idx)

            # Skip this line if condition is not met
            if not exp_format.need_loop and exp_format.condition_line:
                condition = safe_eval(
                    exp_format.condition_line, globals_dict=globals_dict
                )
                if not condition:
                    continue

            # Add value to the set of processed values
            if exp_format.match_group:
                processed_match.add(exp_format.match_group)

            if exp_format.need_loop:
                self._process_loop(
                    exp_format, exp_format_lines, globals_dict, text_parts
                )
                continue

            # Get value from instruction
            text_line = exp_format._get_value(globals_dict)
            text_parts.append(text_line)

            if exp_format.end_line:
                # TODO: Change this to configurable
                text_parts.append("\r\n")

        text = "".join(text_parts)
        return text

    def _process_loop(self, exp_format, exp_format_lines, globals_dict, text_parts):
        # Get all lines that match the current group
        wht_cert = False
        for idx_line, line in enumerate(self.export_line_ids):
            # Change the value of the line in the globals_dict
            payment = line.payment_id
            if hasattr(payment, "wht_cert_ids"):
                wht_cert = payment.wht_cert_ids

            globals_dict_line = self._update_global_dict(
                globals_dict,
                line=line,
                idx_line=idx_line,
                wht_cert=wht_cert,
                invoices=payment.reconciled_bill_ids,
            )

            # search only lines that match the current group and condition
            # filter in loop because we need to check condition_line
            exp_format_line_group = exp_format_lines.filtered(
                lambda l: l.match_group == exp_format.match_group
                and (
                    not l.condition_line
                    or safe_eval(l.condition_line, globals_dict=globals_dict_line)
                )
            )

            processed_subloop = set()

            for exp_format_line in exp_format_line_group:
                # Sub-loop logic
                if exp_format_line.sub_loop:
                    self._process_sub_loop(
                        exp_format_line,
                        exp_format_line_group,
                        globals_dict_line,
                        text_parts,
                        processed_subloop,
                    )
                    continue

                # Get value from instruction
                text_line = exp_format_line._get_value(globals_dict_line)
                text_parts.append(text_line)

                if exp_format_line.end_line:
                    # TODO: Change this to configurable
                    text_parts.append("\r\n")
        return text_parts

    def _process_sub_loop(
        self,
        exp_format_line,
        exp_format_line_group,
        globals_dict_line,
        text_parts,
        processed_subloop,
    ):
        if exp_format_line.sub_value_loop not in processed_subloop:
            processed_subloop.add(exp_format_line.sub_value_loop)

            exp_format_sub_line_group = exp_format_line_group.filtered(
                lambda l: l.sub_value_loop == exp_format_line.sub_value_loop
            )
            sub_lines = safe_eval(
                exp_format_line.sub_value_loop, globals_dict=globals_dict_line
            )

            for idx_sub_line, sub_line in enumerate(sub_lines):
                for exp_format_sub_line in exp_format_sub_line_group:
                    # Update globals_dict for sub-loop
                    globals_dict_sub_line = self._update_global_dict(
                        globals_dict_line, sub_line=sub_line, idx_sub_line=idx_sub_line
                    )

                    # Get value from sub-instruction
                    sub_text_line = exp_format_sub_line._get_value(
                        globals_dict_sub_line
                    )
                    text_parts.append(sub_text_line)

                    if exp_format_sub_line.end_line:
                        # TODO: Change this to configurable
                        text_parts.append("\r\n")
        return text_parts

    def _export_bank_payment_text_file(self):
        self.ensure_one()
        if self.bank:
            return self._generate_bank_payment_text()
        return "Demo Text File. You must config `Bank Export Format` First."

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

    # ====================== Function Common Text File ======================

    def _get_receiver_address(self, object_address):
        receiver_address = " ".join(
            [
                object_address.street or "",
                object_address.street2 or "",
                object_address.city or "",
                object_address.zip or "",
            ]
        )
        return receiver_address

    def _get_address(self, object_address, max_length):
        receiver_address = self._get_receiver_address(object_address)
        address = receiver_address[:max_length]
        return address

    def _get_amount_wht_invoice(self, inv, line):
        """get amount wht from invoice"""
        amount_wht = 0.0
        if hasattr(inv.invoice_line_ids, "wht_tax_id"):
            wht_lines = inv.invoice_line_ids.filtered("wht_tax_id")
            amount_wht = wht_lines._get_wht_amount(
                self.env.company.currency_id, line.payment_date
            )[1]
        return amount_wht
