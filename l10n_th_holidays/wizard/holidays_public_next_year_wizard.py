# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from odoo import api, models, fields


class HolidaysPublicNextYearWizard(models.TransientModel):
    _inherit = 'public.holidays.next.year.wizard'

    @api.multi
    def create_public_holidays(self):
        self.ensure_one()
        res = super().create_public_holidays()
        new_calendar = self.env['hr.holidays.public'].browse(res['res_id'])
        # Delete substitute days
        substitute_days = new_calendar.line_ids.filtered(
            lambda r: not r.variable_date and 'Substitute for' in r.name
        )
        substitute_days.unlink()
        # Add substitute days
        for line in self.pending_lines:
            date = fields.Date.from_string(line.date)
            last_day_of_year = date.replace(month=12, day=31)
            if date.weekday() > 4 and date != last_day_of_year:
                while date.weekday() > 4 or \
                        date in new_calendar.line_ids.mapped('date'):
                    date += relativedelta(days=1)
                new_vals = {
                    'name': 'Substitute for ' + line.name,
                    'year_id': new_calendar.id,
                    'date': fields.Date.to_string(date),
                    'variable_date': False,
                }
                line.line_id.copy(new_vals)
        return res
