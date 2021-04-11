# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models
from types import CodeType

STATUS = [('draft', 'Draft'), ('open', 'Running'),
          ('close', 'Close'), ('removed', 'Removed')]


class AssetRegisterExportXslx(models.AbstractModel):
    _name = 'report.asset_register_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _write_ws_filter(self, ws, row_pos, ws_params, col_specs_section=None,
                         render_space=None, default_format=None):
        col_specs = ws_params.get('col_filters')
        wl = ws_params.get('data_filters') or []
        pos = 0
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

    def _get_ws_params(self, wb, data, assets):
        asset_template = {
            '01_profile_name': {
                'header': {
                    'value': 'รหัสกลุ่มสินทรัพย์',
                },
                'data': {
                    'value': self._render('asset.profile_id.name'),
                },
                'width': 25,
            },
            '02_name': {
                'header': {
                    'value': 'ชื่อสินทรัพย์',
                },
                'data': {
                    'value': self._render('asset.name'),
                },
                'width': 20,
            },
            '03_date_start': {
                'header': {
                    'value': 'วันที่เริ่มคำนวณค่าเสื่อม',
                },
                'data': {
                    'value': self._render('asset.date_start'),
                    'type': 'datetime',
                    'format': self.format_tcell_date_left,
                },
                'width': 13,
            },
            '04_purchase_value': {
                'header': {
                    'value': 'ราคาทรัพย์สินที่ซื้อหรือได้มา',
                },
                'data': {
                    'value': self._render('asset.purchase_value'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '05_accumulated_bf': {
                'header': {
                    'value': 'มูลคาตนทุนในวันสุดทายของรอบระยะบัญชีก่อน',
                },
                'data': {
                    'value': self._render('asset.accumulated_bf'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '06_percent_depreciation': {
                'header': {
                    'value': 'อัตราร้อยละ',
                },
                'data': {
                    'value': self._render('asset.percent_depreciation'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 7,
            },
            '07_depreciation_base': {
                'header': {
                    'value': 'มูลค่าที่คิดค่าเสื่อม',
                },
                'data': {
                    'value': self._render('asset.depreciation_base'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '08_salvage_value': {
                'header': {
                    'value': 'ราคาซาก',
                },
                'data': {
                    'value': self._render('asset.salvage_value'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '09_depreciation': {
                'header': {
                    'value': 'ค่าเสื่อมราคาที่หักในรอบระยะเวลาบัญชีนี้',
                },
                'data': {
                    'value': self._render('asset.depreciation'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '10_accumulated_cf': {
                'header': {
                    'value': 'ค่าเสื่อมราคาสะสมจนถึงปัจจุบัน',
                },
                'data': {
                    'value': self._render('asset.accumulated_cf'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '11_present_residual': {
                'header': {
                    'value':
                        'มูลค่าต้นทุนหลังหักค่าเสื่อมราคาแล้ว จนถึงปัจจุบัน',
                },
                'data': {
                    'value': self._render('present_residual'),
                    'type': 'number',
                    'format': self.format_tcell_amount_right,
                },
                'width': 15,
            },
            '12_code': {
                'header': {
                    'value': 'เอกสารอ้างอิง',
                },
                'data': {
                    'value': self._render('code'),
                },
                'width': 15,
            },
            '13_note': {
                'header': {
                    'value': 'หมายเหตุ',
                },
                'data': {
                    'value': self._render('note'),
                },
                'width': 15,
            },
        }

        asset_filters = {
            '1_filter1': {
                'header': {
                    'value': 'Date range filter',
                },
                'data': {
                    'value': '%s to %s' % (assets.date_from, assets.date_to),
                },
            },
            '2_filter2': {
                'header': {
                    'value': 'Asset filter',
                },
                'data': {
                    'value': assets.asset_ids and
                    assets._get_asset_ids(assets.asset_ids) or '',
                },
            },
            '3_filter3': {
                'header': {
                    'value': 'Asset Profile filter',
                },
                'data': {
                    'value': assets.asset_profile_ids and
                    assets._get_asset_ids(assets.asset_profile_ids) or '',
                },
            },
            '4_filter4': {
                'header': {
                    'value': 'Asset Status',
                },
                'data': {
                    'value': assets.asset_status and
                    dict(STATUS)[assets.asset_status] or '',
                },
            }
        }
        ws_params = {
            'ws_name': 'Asset Register',
            'generate_ws_method': '_assets_report',
            'title': 'Asset Register - %s - %s' % (
                assets.company_id.name,
                assets.company_id.currency_id.name),
            'data_filters': [x for x in sorted(asset_filters.keys())],
            'col_filters': asset_filters,
            'wanted_list': [x for x in sorted(asset_template.keys())],
            'col_specs': asset_template,
        }

        return [ws_params]

    def _assets_report(self, workbook, ws, ws_params, data, assets):
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
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_center)
        ws.freeze_panes(row_pos, 0)

        for asset in assets.results:
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='data',
                render_space={
                    'asset': asset,
                    'present_residual':
                        asset.purchase_value - asset.accumulated_cf,
                    'code': asset.code or '',
                    'note': asset.note or '',
                },
                default_format=self.format_tcell_left)
