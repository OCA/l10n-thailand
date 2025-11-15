# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


def post_init_hook(env):
    """Set enforce_subdistrict and enforce_city to True for Thailand"""
    env.ref("base.th").write(
        {
            "enforce_subdistrict": True,
            "enforce_cities": True,
        }
    )
