# Copyright 2023 Ross Golder <ross@golder.org>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_file(self, data_file):
        """Parse a Kasikorn KBiz CSV statement file."""
        try:
            parser = self.env["account.statement.import.kbiz.parser"]
            _logger.debug("Try parsing with KBiz.")
            return parser.parse(data_file)
        except ValueError:
            _logger.debug(
                "Statement file was not a KBiz CSV file.", exc_info=True)
        return super()._parse_file(data_file)
