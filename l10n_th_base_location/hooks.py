# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


def post_init_hook(env):
    # Thailand can city duplicate, But subdistrict is not allow duplicate
    # env.cr.execute("""
    #     ALTER TABLE res_city DROP CONSTRAINT IF EXISTS name_state_country_uniq;
    # """)
    pass
