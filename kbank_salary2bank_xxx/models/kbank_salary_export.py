# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from datetime import datetime
from odoo import models, fields, api


class KBankSalaryExport(models.Model):
    """ Model storing final salary for export to text file """
    _name = 'kbank.salary.export'
    _description = 'KBank Salary Export'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_code = fields.Char(
        string='Company Code',
        required=True,
    )
    trans_type = fields.Char(
        string='Trans-Type',
        required=True,
    )
    trans_type_batch = fields.Char(
        string='Trans-Type (Batch)',
        required=True,
    )
    trans_date = fields.Date(
        string='Date',
        required=True,
    )
    export_line_ids = fields.One2many(
        comodel_name='kbank.salary.export.line',
        inverse_name='export_id',
        string='Export Lines',
    )
    note = fields.Text(
        string='Notes',
    )

    @api.multi
    def generate_export_lines(self):
        """ Read all active employee, to each salary line """
        Employee = self.env['hr.employee']
        employees = Employee.search([])
        for rec in self:
            rec.export_line_ids.unlink()
            lines = []
            trans_no = 1
            # Employee Lines
            for employee in employees:
                vals = {'batch_control': False,
                        'trans_no': trans_no,
                        'trans_type': rec.trans_type,
                        'company_code': rec.company_code,
                        'payee_account': employee.bank_account_id.acc_number,
                        'amount': False,
                        'trans_date': rec.trans_date,
                        'title': False,
                        'payee_name': employee.name, }
                lines.append((0, 0, vals))
                trans_no += 1
            # Final Line
            vals = {'batch_control': True,  # Will affect comput of amount
                    'trans_no': trans_no,
                    'trans_type': rec.trans_type_batch,
                    'company_code': rec.company_code,
                    'payee_account': '0000000000',
                    'amount': False,  # to be computed
                    'trans_date': False,  # to be computed
                    'title': False,
                    'payee_name': False, }
            lines.append((0, 0, vals))
            rec.write({'export_line_ids': lines})
        return True


class KBankSalaryExportLine(models.Model):
    _name = 'kbank.salary.export.line'
    _description = 'KBank Salary Export Lines'

    export_id = fields.Many2one(
        comodel_name='kbank.salary.export',
        string='Export',
        index=True,
        readonly=True,
        ondelete='cascade',
    )
    batch_control = fields.Boolean(
        string='Page Control',
        default=False,
        help="Signify last export line, which act as batch control",
    )
    trans_no = fields.Integer(
        string='Trans-No',
    )
    trans_type = fields.Char(
        string='Trans-Type',
        readonly=True,
    )
    company_code = fields.Char(
        string='Company Code',
        readonly=True,
    )
    payee_account = fields.Char(
        string='Acct-No',
    )
    amount = fields.Float(
        string='Amount',
    )
    amount_str = fields.Char(
        string='Amount',
        compute='_compute_amount_str',
    )
    trans_date = fields.Date(
        string='Trans-Date',
    )
    trans_date_str = fields.Char(
        string='Trans-Date',
        compute='_compute_trans_date_str',
    )
    title = fields.Char(
        string='Title',
    )
    payee_name = fields.Char(
        string='Payee Name'
    )

    @api.multi
    def _compute_amount_str(self):
        amount_total = 0.0
        for rec in self:
            if not rec.batch_control:
                rec.amount_str = str(int(rec.amount * 100)).zfill(15)
                amount_total += rec.amount
            else:
                rec.amount_str = str(int(amount_total * 100)).zfill(15)
        return True

    @api.multi
    def _compute_trans_date_str(self):
        for rec in self:
            if rec.trans_date:
                trans_date = datetime.strptime(rec.trans_date, "%Y-%m-%d")
                rec.trans_date_str = trans_date.strftime('%y%m%d')
            else:
                rec.trans_date_str = '000000'
        return True
