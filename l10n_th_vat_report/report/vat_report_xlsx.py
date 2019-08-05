import logging
from odoo import models
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class ReportVatReportXlsx(models.TransientModel):
    _name = 'report.l10n_th_vat_report.report_vat_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    @staticmethod
    def _print_vat_report(l, sheet, row):
        i = row
        sheet.write(i, 0, i-6)
        sheet.write(i, 1, str(l.date) or '')
        sheet.write(i, 2, l.tax_invoice or '')
        sheet.write(i, 3, l.partner_id.display_name or '')
        sheet.write(i, 4, l.partner_id.vat or '')
        sheet.write(i, 5, l.partner_id.branch or '')
        sheet.write(i, 6, l.base_amount or 0.00)
        sheet.write(i, 7, l.tax_amount or 0.00)
        sheet.write(i, 8, l.name or '')
        i += 1
        return i

    def generate_xlsx_report(self, workbook, data, objects):
        workbook.set_properties({
            'comments': 'Created with Python and XlsxWriter from Odoo 12.0'})
        sheet = workbook.add_worksheet(_('VAT Report'))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        sheet.set_column(0, 0, 6)
        sheet.set_column(1, 2, 18)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 8, 18)

        title_style = workbook.add_format({'bold': True,
                                           'bg_color': '#ADDFFF',
                                           'bottom': 1})
        sheet_title = [_('#'),
                       _('Date'),
                       _('Number'),
                       _('Cust./Sup.'),
                       _('Tax ID'),
                       _('Branch ID'),
                       _('Base Amount'),
                       _('Tax Amount'),
                       _('Doc Ref.'),
                       ]
        sheet.write_row(6, 0, sheet_title, title_style)

        for o in objects:
            # Write header
            head_format = workbook.add_format({'font_size': 'font_size+3',
                                               'bold': 1,
                                               'align': 'center'})
            if o.tax_id.type_tax_use == "sale":
                sheet.merge_range('A2:I2', 'Sale VAT Report', head_format)
            else:
                sheet.merge_range('A2:I2', 'Purchase VAT Report', head_format)
            sheet.write_row(
                3, 1, [_('Period :'), (o.date_range_id.display_name) or ''])
            sheet.write_row(
                4, 1, [_('Partner :'), (o.company_id.display_name) or ''])
            sheet.write_row(
                3, 5, [_('Tax ID :'), (o.company_id.partner_id.vat) or ''])
            sheet.write_row(
                4, 5, [_('Branch ID :'),
                        (o.company_id.partner_id.branch) or ''])

            i = 7
            for l in o.results:
                i = self._print_vat_report(l, sheet, i)
