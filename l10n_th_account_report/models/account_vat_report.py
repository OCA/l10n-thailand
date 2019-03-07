# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields


class AccountVatReport(models.Model):
    _name = 'account.vat.report'
    _description = 'Account VAT Report'
    _auto = False
    _order = 'date, partner_id'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
    )
    name = fields.Char(
        string='Journal Entry',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
    )
    tax_invoice = fields.Char(
        string='Tax Invoice',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    date = fields.Date(
        string='Date',
    )
    base_amount = fields.Float(
        string='Base Amount',
    )
    tax_amount = fields.Float(
        string='Tax Amount',
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                select
                    aml.id as id, am.company_id, am.name,
                    aml.account_id, aml.tax_invoice, aml.partner_id,
                    aml.date, aml.tax_base_amount as base_amount,
                    abs(aml.balance) tax_amount
                    from account_move_line aml
                    join account_move am on aml.move_id = am.id
                    where tax_line_id is not null
            )
        """ % (self._table, ))
