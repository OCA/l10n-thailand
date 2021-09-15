# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PersonalIncomeTaxMoveYearly(models.Model):
    _name = "pit.move.yearly"
    _description = "Personal Income Tax by Year"
    _auto = False

    payment_id = fields.Many2one(comodel_name="account.payment")
    partner_id = fields.Many2one(comodel_name="res.partner")
    calendar_year = fields.Char(string="Calendar Year")
    amount_income = fields.Float(string="Income")
    amount_wt = fields.Float(string="Withholding Amount")

    @property
    def _table_query(self):
        return "{}".format(self._get_sql())

    def _select_pit_yearly(self):
        return """
            ROW_NUMBER() OVER() AS id,
            pm.partner_id, pm.calendar_year, pm.payment_id,
            pm.amount_income, pm.amount_wt
        """

    def _from_pit_yearly(self):
        return """
            from pit_move pm
            left outer join account_payment ap on ap.id = pm.payment_id
            left outer join account_move am on am.id = ap.move_id
        """

    def _where_pit_yearly(self):
        """ Related from pit on vender """
        if self._context.get("active_model") == "res.partner":
            partner_id = self.env["res.partner"].browse(
                self._context.get("active_id", [])
            )
            if len(partner_id.pit_line) > 1:
                pit = "in {}".format(tuple(partner_id.pit_line.ids))
            else:
                pit = "= {}".format(partner_id.pit_line.id or 0)
            return """ where pm.id {} """.format(pit)
        return ""

    def _get_sql(self):
        return "select {} {} {}".format(
            self._select_pit_yearly(),
            self._from_pit_yearly(),
            self._where_pit_yearly(),
        )
