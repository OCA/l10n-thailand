# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models
from types import CodeType


class BankStatementExportXslx(models.AbstractModel):
    _name = 'report.bank_statement_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _compute_data(self, ws, row_pos, col_specs, wl, pos,
                      col_specs_section=None, render_space=None,
                      default_format=None):
        for col in wl:
            colspan = col_specs[col].get('colspan') or 1
            cell_spec = col_specs[col].get(col_specs_section) or {}
            cell_value = cell_spec.get('value')
            cell_type = cell_spec.get('type')
            cell_format = cell_spec.get('format') or default_format
            if not cell_type:
                cell_type = 'string'
            colspan = cell_spec.get('colspan') or colspan
            args_pos = [row_pos, pos]
            args_data = [cell_value]
            if cell_format:
                if isinstance(cell_format, CodeType):
                    cell_format = self._eval(cell_format, render_space)
                args_data.append(cell_format)
            ws_method = getattr(ws, 'write_%s' % cell_type)
            args = args_pos + args_data
            ws_method(*args)
            pos += colspan
        return row_pos + 1

    def _write_ws_filter(self, ws, row_pos, ws_params, col_specs_section=None,
                         render_space=None, default_format=None):
        col_specs = ws_params.get('col_filters')
        wl = ws_params.get('data_filters') or []
        pos = 0
        row_pos = self._compute_data(
            ws, row_pos, col_specs, wl, pos, col_specs_section,
            render_space, default_format)
        return row_pos

    def _get_line_initial(self, bank_statement, field):
        move_line = self.env['account.move.line'].search(
            [('date_maturity', '<', bank_statement.date_from),
             ('journal_id', '=', bank_statement.bank_account_id.id),
             ('account_id', 'in',
             [bank_statement.bank_account_id.default_debit_account_id.id,
              bank_statement.bank_account_id.default_credit_account_id.id])]
        ).mapped(field)
        if move_line:
            return sum(move_line)
        return False

    def _write_line_initial(self, ws, row_pos, ws_params, bank_statement,
                            col_specs_section=None, render_space=None,
                            default_format=None):
        col_specs = ws_params.get('col_initial_balance')
        wl = ws_params.get('data_initial_balance') or []
        pos = 0
        row_pos = self._compute_data(
            ws, row_pos, col_specs, wl, pos, col_specs_section,
            render_space, default_format)
        return row_pos

    def _write_footer(self, ws, row_pos, ws_params, col_specs_section=None,
                      render_space=None, default_format=None):
        wl = ws_params.get('data_initial_balance') or []
        pos = 0
        balance = render_space.get('balance', 0.0)
        total_credit = render_space.get('total_credit', 0.0)
        total_debit = render_space.get('total_debit', 0.0)
        total_currency = render_space.get('total_currency', 0.0)
        # Create string
        ws.write_row(row_pos, pos,
                     [total_credit if x == '05_credit' else
                      total_debit if x == '06_debit' else
                      balance if x == '07_balance' else
                      total_currency if x == '08_currency' else ''
                      for x in wl], default_format)

    def _get_ws_params(self, wb, data, bank_statement):
        bank_statement_template = {
            '01_date_maturity': {
                'header': {
                    'value': 'Date',
                },
                'data': {
                    'value': self._render('statement.date_maturity'),
                    'type': 'datetime',
                    'format': self.format_tcell_date_center,
                },
                'width': 15,
            },
            '02_description': {
                'header': {
                    'value': 'Description',
                },
                'data': {
                    'value': self._render('statement.name'),
                },
                'width': 30,
            },
            '03_partner': {
                'header': {
                    'value': 'Partner',
                },
                'data': {
                    'value': self._render('partner'),
                },
                'width': 25,
            },
            '04_ref': {
                'header': {
                    'value': 'Ref.',
                },
                'data': {
                    'value': self._render('statement.ref'),
                },
                'width': 15,
            },
            '05_credit': {
                'header': {
                    'value': 'Withdrawals',
                },
                'data': {
                    'value': self._render('statement.credit'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '06_debit': {
                'header': {
                    'value': 'Deposits',
                },
                'data': {
                    'value': self._render('statement.debit'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '07_balance': {
                'header': {
                    'value': 'Balance',
                },
                'data': {
                    'value': self._render('balance'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '08_currency': {
                'header': {
                    'value': 'Amount Currency',
                },
                'data': {
                    'value': self._render('statement.amount_currency'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
        }

        bank_statement_filters = {
            '01_filter': {
                'header': {
                    'value': 'Date range filter',
                },
                'data': {
                    'value': '%s to %s' %
                    (bank_statement.date_from, bank_statement.date_to),
                },
            },
            '02_filter': {
                'header': {
                    'value': 'Bank Account',
                },
                'data': {
                    'value': bank_statement.bank_account_id.display_name,
                },
            },
        }

        bank_statement_initial = {
            '01_date': {
                'data': {
                    'value': bank_statement.date_from,
                    'type': 'datetime',
                    'format': self.format_tcell_date_center,
                },
            },
            '02_name': {
                'data': {
                    'value': 'Initial Balance',
                },
            },
            '03_partner': {
                'data': {
                    'value': '',
                },
            },
            '04_ref': {
                'data': {
                    'value': '',
                },
            },
            '05_credit': {
                'data': {
                    'value': self._get_line_initial(bank_statement, 'credit'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
            },
            '06_debit': {
                'data': {
                    'value': self._get_line_initial(bank_statement, 'debit'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
            },
            '07_balance': {
                'data': {
                    'value': self._get_line_initial(bank_statement, 'balance'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
            },
            '08_currency': {
                'data': {
                    'value': self._get_line_initial(
                        bank_statement, 'amount_currency'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
            },
        }
        ws_params = {
            'ws_name': 'Bank Statement',
            'generate_ws_method': '_bank_statement_report',
            'title': 'Bank Statement - %s - %s' % (
                bank_statement.company_id.name,
                bank_statement.company_id.currency_id.name),
            'data_filters': [x for x in sorted(bank_statement_filters.keys())],
            'col_filters': bank_statement_filters,
            'data_initial_balance':
                [x for x in sorted(bank_statement_initial.keys())],
            'col_initial_balance': bank_statement_initial,
            'wanted_list': [x for x in sorted(bank_statement_template.keys())],
            'col_specs': bank_statement_template,
        }

        return [ws_params]

    def _bank_statement_report(
            self, workbook, ws, ws_params, data, bank_statement):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)
        # Filters data
        row_pos = self._write_ws_filter(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)
        row_pos = self._write_ws_filter(
            ws, row_pos, ws_params, col_specs_section='data',
            default_format=self.format_tcell_left)
        row_pos += 1

        # Create header line
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_center)
        ws.freeze_panes(row_pos, 0)
        # Create Initial Balance First line
        row_pos = self._write_line_initial(
            ws, row_pos, ws_params, bank_statement, col_specs_section='data',
            default_format=self.format_tcell_left)
        # Create lines
        balance = self._get_line_initial(bank_statement, 'balance')
        total_credit = self._get_line_initial(bank_statement, 'credit')
        total_debit = self._get_line_initial(bank_statement, 'debit')
        total_currency = \
            self._get_line_initial(bank_statement, 'amount_currency')
        for statement in bank_statement.results:
            total_credit += statement.credit
            total_debit += statement.debit
            balance += statement.balance
            total_currency += statement.amount_currency
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='data',
                render_space={
                    'statement': statement,
                    'partner': statement.partner_id.name or '',
                    'balance': balance,
                },
                default_format=self.format_tcell_left)
        # Create Footer line
        row_pos = self._write_footer(
            ws, row_pos, ws_params, col_specs_section='data',
            render_space={
                'balance': balance,
                'total_credit': total_credit,
                'total_debit': total_debit,
                'total_currency': total_currency,
            },
            default_format=self.format_theader_yellow_amount_right
        )
