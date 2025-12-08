# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


def post_init_hook(env):
    """Set enforce_subdistrict, enforce_city and address format for Thailand"""
    address_format = "%(street)s\n%(street2)s\n%(subdistrict)s %(city)s\
        \n%(state_name)s %(zip)s\n%(country_name)s"
    env.ref("base.th").write(
        {
            "enforce_subdistrict": True,
            "enforce_cities": True,
            "address_format": address_format,
        }
    )
