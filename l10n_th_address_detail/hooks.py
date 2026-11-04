# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from .models.res_partner import L10N_TH_STREET_FORMAT


def post_init_hook(env):
    """Select the Thai districts and sub-districts on the addresses, and show
    the default Thai street format on Thailand, ready to be adapted"""
    env.ref("base.th").write(
        {"enforce_cities": True, "l10n_th_street_format": L10N_TH_STREET_FORMAT}
    )


def uninstall_hook(env):
    """The Thai districts are removed with the module"""
    env.ref("base.th").enforce_cities = False
