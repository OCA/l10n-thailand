# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Activate Thai language for use in amount_to_text"""
    th_lang = (
        env["res.lang"]
        .sudo()
        .search([("code", "=", "th_TH"), ("active", "=", False)], limit=1)
    )

    if th_lang:
        th_lang.write({"active": True})
        _logger.info(f"Activated Thai language: {th_lang.code}")
    else:
        _logger.info("Thai language (th_TH) not found in res.lang!")
