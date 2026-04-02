# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class BankPaymentExport(models.Model):
    _name = "bank.payment.export"
    _inherit = ["mail.thread", "mail.activity.mixin", "bank.payment.export.common"]
    _description = "Bank Payment Export File"
    _order = "name desc"
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
        tracking=True,
    )
    profile_id = fields.Many2one(
        comodel_name="bank.payment.profile",
        string="Profile",
        tracking=True,
        check_company=True,
    )
    bank_template_id = fields.Many2one(
        comodel_name="bank.template",
        tracking=True,
    )
    domain_payment_method = fields.Many2one(
        comodel_name="account.payment.method",
        default=lambda self: self.env.ref("account.account_payment_method_manual_out"),
    )
    effective_date = fields.Date(copy=False)
    export_line_ids = fields.One2many(
        comodel_name="bank.payment.export.line",
        inverse_name="payment_export_id",
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
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Exported"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
        default="draft",
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )

    @api.onchange("profile_id")
    def _onchange_profile_id(self):
        """Update field following bank payment profile"""
        profile = self.profile_id
        if not profile:
            return

        self.bank = profile.bank
        update_vals = {}

        for line in profile.line_ids:
            field = line.field_id
            value = line.value

            if field.ttype in ["many2one", "many2many"]:
                # If value is digit, use directly as id, else search by name
                if value and value.isdigit():
                    res_id = int(value)
                else:
                    res_id = (
                        self.env[field.relation]
                        .search([("name", "=", value)], limit=1)
                        .id
                    )

                # many2many field requires a list of commands, not an integer ID
                if field.ttype == "many2many" and res_id:
                    value = [Command.set([res_id])]
                else:
                    value = res_id

            update_vals[field.name] = value

        if update_vals:
            self.update(update_vals)

    @api.depends("export_line_ids", "export_line_ids.state")
    def _compute_total_amount(self):
        for rec in self:
            # Amount total without line rejected
            rec.total_amount = sum(
                rec.export_line_ids.filtered(
                    lambda line: line.state != "reject"
                ).mapped("payment_amount")
            )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = sequence.next_by_code("bank.payment.export") or "/"
        return super().create(vals_list)

    def unlink(self):
        """Check state draft can delete only."""
        if any(rec.state != "draft" for rec in self):
            raise UserError(
                self.env._("You are trying to delete a record state is not 'draft'")
            )
        return super().unlink()

    def _domain_payment_id(self):
        """Condition search all payment
        1. Currency same as company currency
        2. Company same as company_id
        3. Payment not exported and state 'paid' only
        4. Payment method must be 'Manual' on Vendor Payment
        5. Journal payment must be type 'Bank' only
        """
        domain = [
            ("export_status", "=", "draft"),
            ("state", "=", "paid"),
            ("payment_method_id", "=", self.domain_payment_method.id),
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
        return f"{self.name}"

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
            "lines": self.export_line_ids,
            "today": today,
            "today_datetime": today_datetime,
        }
        return globals_dict

    def _update_global_dict(self, globals_dict, **kwargs):
        """Update global dict with kwargs"""
        globals_dict.update(kwargs)
        return globals_dict

    def _get_payment_wht_certs(self, payment):
        """Return the payment's WHT certs, or False if the WHT module is missing."""
        return getattr(payment, "wht_cert_ids", False)

    def _get_data_level_payment(self, active_lines, parent_ctx):
        # If parent context already contains payment data,
        # reuse it instead of re-iterating all payment lines.
        # This prevents duplicate lines when a child section
        # (e.g. Footer) has the same data_level as its parent.
        if parent_ctx.get("payment"):
            return [parent_ctx]
        return [
            {
                "line": line,
                "idx_payment": idx,
                "payment": line.payment_id,
                "invoices": line.payment_id.reconciled_bill_ids,
                "wht_certs": self._get_payment_wht_certs(line.payment_id),
            }
            for idx, line in enumerate(active_lines)
        ]

    def _get_data_level_invoice(self, active_lines, parent_ctx):
        items = []
        if parent_ctx.get("payment"):
            payment = parent_ctx["payment"]
            invoices = payment.reconciled_bill_ids or [False]
            for idx, inv in enumerate(invoices):
                ctx = dict(parent_ctx)
                ctx.update(
                    {
                        "invoice": inv,
                        "idx_invoice": idx,
                    }
                )
                items.append(ctx)
        else:
            for idx, line in enumerate(active_lines):
                payment = line.payment_id
                invoices = payment.reconciled_bill_ids or [False]
                for idx_inv, inv in enumerate(invoices):
                    items.append(
                        {
                            "line": line,
                            "idx_payment": idx,
                            "payment": payment,
                            "invoices": payment.reconciled_bill_ids,
                            "invoice": inv,
                            "idx_invoice": idx_inv,
                            "wht_certs": self._get_payment_wht_certs(payment),
                        }
                    )
        return items

    def _get_data_level_wht(self, active_lines, parent_ctx):
        items = []
        if parent_ctx.get("payment"):
            payment = parent_ctx["payment"]
            whts = self._get_payment_wht_certs(payment) or [False]
            for idx_wht, wht in enumerate(whts):
                ctx = dict(parent_ctx)
                ctx.update(
                    {
                        "wht_cert": wht,
                        "idx_wht": idx_wht,
                    }
                )
                items.append(ctx)
        else:
            for idx, line in enumerate(active_lines):
                payment = line.payment_id
                whts = self._get_payment_wht_certs(payment) or [False]
                for idx_wht, wht in enumerate(whts):
                    items.append(
                        {
                            "line": line,
                            "idx_payment": idx,
                            "payment": payment,
                            "invoices": payment.reconciled_bill_ids,
                            "wht_certs": self._get_payment_wht_certs(payment),
                            "wht_cert": wht,
                            "idx_wht": idx_wht,
                        }
                    )
        return items

    def _get_data_level_custom(self, active_lines, group):
        items = []
        for idx_line, line in enumerate(active_lines):
            globals_dict = self._set_global_dict()
            globals_dict = self._update_global_dict(
                globals_dict,
                payment_line=line,
                payment=line.payment_id,
                idx_payment=idx_line,
            )

            try:
                custom_items = safe_eval(
                    group["custom_iterable"], globals_dict=globals_dict
                )
            except Exception:
                custom_items = []

            if not custom_items:
                custom_items = [False]

            for idx_sub, sub_item in enumerate(custom_items):
                ctx = {
                    "payment_line": line,
                    "payment": line.payment_id,
                    "sub_line": sub_item,
                    "idx_sub_line": idx_sub,
                }
                items.append(ctx)

        return items

    def _get_group_data_items(self, group, parent_ctx=None):
        self.ensure_one()

        data_level = group["data_level"]

        # DOCUMENT
        if data_level == "document":
            return [{}]

        active_lines = self.export_line_ids.filtered(
            lambda line: line.state != "reject"
        )
        parent_ctx = parent_ctx or {}

        # PAYMENT
        if data_level == "payment":
            return self._get_data_level_payment(active_lines, parent_ctx)

        # INVOICE
        if data_level == "invoice":
            return self._get_data_level_invoice(active_lines, parent_ctx)

        # WHT
        if data_level == "wht":
            return self._get_data_level_wht(active_lines, parent_ctx)

        # CUSTOM
        # NOTE: Not yet tested
        if data_level == "custom":
            return self._get_data_level_custom(active_lines, group)

        return []

    def _render_lines(self, lines, line_ending, parent_ctx=None):
        ctx = parent_ctx or {}

        globals_dict = self._set_global_dict()
        parts = []
        has_visible = False

        for line in lines:
            if line.section_id:
                globals_dict = self._update_global_dict(globals_dict, **ctx)

            if line.condition:
                try:
                    if not safe_eval(line.condition, globals_dict=globals_dict):
                        continue
                except Exception:
                    continue

            value = line._get_value(globals_dict)
            parts.append(value)
            has_visible = True

        if has_visible or not lines:
            return ["".join(parts), line_ending]

        return []

    def _execute_section(
        self, section, section_lines_map, text_parts, line_ending, parent_ctx=None
    ):
        dummy_group = {
            "data_level": section.data_level,
            "custom_iterable": getattr(section, "custom_iterable", False),
        }
        data_items = self._get_group_data_items(dummy_group, parent_ctx)

        for item_ctx in data_items:
            # Render lines
            lines = section_lines_map.get(section.id, [])
            if lines:
                rendered = self._render_lines(lines, line_ending, parent_ctx=item_ctx)
                text_parts.extend(rendered)

            # Execute Children
            for child in section.child_ids.sorted("sequence"):
                self._execute_section(
                    child,
                    section_lines_map,
                    text_parts,
                    line_ending,
                    parent_ctx=item_ctx,
                )

    def _generate_bank_payment_text(self):
        self.ensure_one()

        if not self.bank_template_id:
            raise UserError(self.env._("Bank format not found."))

        template = self.bank_template_id
        line_ending = template._get_line_ending()
        text_parts = []

        # --------------------------------------------------
        # 1. Get template lines
        # --------------------------------------------------
        template_lines = template.template_line_ids.filtered(
            lambda line: line.display_type not in ("line_section", "line_note")
        )

        # --------------------------------------------------
        # 2. Build section -> lines map and collect no-section lines
        # --------------------------------------------------
        section_lines_map = {}
        no_section_lines = []
        sections = {}

        for line in template_lines:
            section = line.section_id
            if not section:
                no_section_lines.append(line)
                continue

            section_lines_map.setdefault(section.id, []).append(line)
            sections[section.id] = section

        # include parent sections (container sections)
        for sec in list(sections.values()):
            p = sec.parent_id
            while p:
                sections[p.id] = p
                p = p.parent_id

        # --------------------------------------------------
        # 3. Build render order (mix no-section lines and root sections)
        # --------------------------------------------------
        root_sections = [s for s in sections.values() if not s.parent_id]

        # Build ordered render items: ("line", line) or ("section", section)
        render_items = []
        for line in no_section_lines:
            render_items.append(("line", line))
        for section in root_sections:
            render_items.append(("section", section))

        # Sort by sequence then id to maintain template order
        render_items.sort(key=lambda item: (item[1].sequence, item[1].id))

        # --------------------------------------------------
        # 4. Execute render items
        # --------------------------------------------------
        for item_type, item in render_items:
            if item_type == "line":
                # No section: render line directly
                text_parts.extend(self._render_lines([item], line_ending))
            else:
                # Section: execute recursively (handles both with/without children)
                self._execute_section(
                    item,
                    section_lines_map,
                    text_parts,
                    line_ending,
                )

        return "".join(text_parts)

    def _export_bank_payment_text_file(self):
        self.ensure_one()
        if self.bank:
            return self._generate_bank_payment_text()
        return "Demo Text File. You must config `Bank Template` First."

    def _check_constraint_line(self):
        # Add condition with line on this function
        self.ensure_one()
        return

    def _check_constraint_confirm(self):
        # Add condition on this function
        for rec in self:
            if not rec.export_line_ids:
                raise UserError(self.env._("You need to add a line before confirm."))
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

    def _get_payment_export_bank(self, payments):
        """Return the single supported bank key shared by the payments, or raise."""
        payment_bic_banks = set(payments.mapped("journal_id.bank_id.bic"))
        supported_banks = self._fields["bank"].get_values(self.env)
        if len(payment_bic_banks) != 1:
            raise UserError(
                self.env._("All selected payments must use the same bank journal.")
            )
        payment_bic_bank = payment_bic_banks.pop()
        if not payment_bic_bank or payment_bic_bank not in supported_banks:
            raise UserError(
                self.env._("No payment export format available for this bank.")
            )
        return payment_bic_bank

    def _get_context_create_bank_payment_export(self, payments):
        ctx = self.env.context.copy()
        export_lines = [
            Command.create({"payment_id": payment}) for payment in payments.ids
        ]
        payment_bank = self._get_payment_export_bank(payments)
        ctx.update(
            {
                "default_profile_id": payments[0].bank_payment_profile_id.id,
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
                today_format = today.strftime("%d/%m/%Y")
                raise UserError(
                    self.env._(
                        f"Effective Date must be more than or equal {today_format}"
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
                    self.env._(
                        "You can not selected bank difference with "
                        "bank journal on payment."
                    )
                )

    def _check_constraint_create_bank_payment_export(self, payments):
        if not payments:
            return

        no_bank = []
        exported = []
        invalid_state = []

        first_profile = payments[0].bank_payment_profile_id
        first_currency = payments[0].currency_id

        for payment in payments:
            if not payment.partner_bank_id:
                no_bank.append(payment.name)

            if payment.export_status != "draft":
                exported.append(payment.name)

            if payment.state != "paid":
                invalid_state.append(payment.name)

            if payment.bank_payment_profile_id != first_profile:
                raise UserError(
                    self.env._("All payments must have the same bank payment profile.")
                )

            if payment.currency_id != first_currency:
                raise UserError(
                    self.env._("You can export bank payments with 1 currency only.")
                )

        if no_bank:
            raise UserError(
                self.env._(
                    "The following payments do not have a Vendor Bank Account:\n%s"
                )
                % "\n".join(no_bank)
            )

        if exported:
            raise UserError(
                self.env._("The following payments have already been exported:\n%s")
                % "\n".join(exported)
            )

        if invalid_state:
            raise UserError(
                self.env._(
                    "You can only export bank payments in state 'paid'.\n"
                    "Invalid payments:\n%s"
                )
                % "\n".join(invalid_state)
            )

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
            "name": self.env._("Bank Payment Export"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "bank.payment.export",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "context": ctx,
        }
