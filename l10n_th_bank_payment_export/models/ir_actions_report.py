# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_text(self, report_ref, docids, data=None):
        report = self._get_report(report_ref)
        if report.report_name == (
            "l10n_th_bank_payment_export.bank_payment_export_text_file"
        ):
            exports = self.env["bank.payment.export"].browse(docids)
            if len(exports) != 1:
                raise UserError(
                    self.env._("Export one bank payment document at a time.")
                )
            # Fixed-width bank files must not pass through HTML escaping.
            return exports._export_bank_payment_text_bytes(), "text"
        return super()._render_qweb_text(report_ref, docids, data=data)
