# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.http import Controller, request, route
from odoo.http.stream import content_disposition


class WhtCertTawiReportsDownloadController(Controller):
    """50 Tawi of withholding tax certificates, as the standard ones of payments"""

    @route(
        '/l10n_th_account_tax/download_tawi_reports/<models("ir.attachment"):attachments>',
        type="http",
        auth="user",
    )
    def download_tawi_reports(self, attachments):
        attachments.check_access("read")
        if not all(
            attachment.res_id and attachment.res_model == "withholding.tax.cert"
            for attachment in attachments
        ):
            return request.not_found()
        if len(attachments) == 1:
            return request.make_response(
                attachments.raw.content,
                [
                    ("Content-Type", attachments.mimetype),
                    ("Content-Length", len(attachments.raw.content)),
                    ("Content-Disposition", content_disposition(attachments.name)),
                    ("X-Content-Type-Options", "nosniff"),
                ],
            )
        filename = request.env._("50_Tawi_Reports") + ".zip"
        content = attachments._build_zip_from_attachments()
        return request.make_response(
            content,
            [
                ("Content-Type", "zip"),
                ("Content-Length", len(content)),
                ("Content-Disposition", content_disposition(filename)),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
