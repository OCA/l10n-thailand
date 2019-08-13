# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class AssetView(models.TransientModel):
    _name = 'asset.view'
    _inherit = 'account.asset'
    _order = 'id'

    asset_id = fields.Many2one(
        comodel_name='account.asset',
    )
    percent_depreciation = fields.Float()
    depreciation = fields.Float()
    accumulated_cf = fields.Float()
    accumulated_bf = fields.Float()


class AssetRegisterReport(models.TransientModel):
    _name = 'report.asset.register'
    _description = 'Report Asset Register'

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    date_from = fields.Date()
    date_to = fields.Date()
    asset_status = fields.Selection(
        [('draft', 'Draft'),
         ('open', 'Running'),
         ('close', 'Close'),
         ('removed', 'Removed')],
    )
    asset_ids = fields.Many2many(
        comodel_name='account.asset',
    )
    asset_profile_ids = fields.Many2many(
        comodel_name='account.asset.profile',
    )
    # Note: report setting
    accum_depre_account_type = fields.Many2one(
        comodel_name='account.account.type',
    )
    depre_account_type = fields.Many2one(
        comodel_name='account.account.type',
    )

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='asset.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def _get_asset_ids(self, obj_ids):
        obj_name = obj_ids.mapped('name')
        name_filter = ', '.join(x for x in obj_name)
        return name_filter

    @api.model
    def _domain_to_where_str(self, domain):
        """ Helper Function for better performance """
        # python v.3+ used str 'instead' of 'basestring'
        where_dom = [" %s %s %s " % (x[0], x[1], isinstance(x[2], str)
                     and "'%s'" % x[2] or x[2]) for x in domain]
        where_str = 'and'.join(where_dom)
        return where_str

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        dom = []
        # Prepare DOM to filter assets
        if self.asset_ids:
            dom += [('id', 'in', tuple(self.asset_ids.ids + [0]))]
        if self.asset_profile_ids:
            dom += [('profile_id', 'in',
                    tuple(self.asset_profile_ids.ids + [0]))]
        if self.asset_status:
            dom += [('state', '=', self.asset_status)]
        # Prepare fixed params
        date_start = self.date_from
        date_end = self.date_to
        fiscalyear_start = self.date_from.strftime('%Y')
        accum_depre_account_ids = self.env['account.account'].search(
            [('user_type_id', '=', self.accum_depre_account_type.id)]).ids
        depre_account_ids = self.env['account.account'].search(
            [('user_type_id', '=', self.depre_account_type.id)]).ids
        where_str = self._domain_to_where_str(dom)
        if where_str:
            where_str = 'and ' + where_str
        sql = self._get_sql(where_str)
        self._cr.execute(sql,
                         (tuple(depre_account_ids), date_start, date_end,
                          tuple(accum_depre_account_ids), date_end,
                          fiscalyear_start,
                          tuple(accum_depre_account_ids), fiscalyear_start))
        asset_results = self._cr.dictfetchall()
        ReportLine = self.env['asset.view']
        for line in asset_results:
            self.results += ReportLine.new(line)

    def _get_sql(self, where_str):
        sql = """
            select a.*, id asset_id,
                -- percent_depreciation
                case when a.method_number != 0
                then (100/cast(a.method_number as numeric))
                else 0 end as percent_depreciation,
                -- depreciation
                (select coalesce(sum(debit-credit), 0.0)
                 from account_move_line ml
                 where account_id in %s  -- depreciation account
                 and ml.date between %s and %s
                 and asset_id = a.id) depreciation,
                -- accumulated_cf
                (select coalesce(sum(credit-debit), 0.0)
                 from account_move_line ml
                 where account_id in %s  -- accumulated account
                 and ml.date <= %s -- date end
                 and asset_id = a.id) accumulated_cf,
                -- accumulated_bf
                case when SUBSTRING(a.date_start :: text,1,4) >= %s
                then 0 else
                (select a.purchase_value - coalesce(sum(credit-debit), 0.0)
                 from account_move_line ml
                 where account_id in %s  -- accumulatedp account
                 and SUBSTRING(ml.date :: text,1,4) < %s -- fiscalyear start
                 and asset_id = a.id) end accumulated_bf
            from
            account_asset a
            where (a.state != 'close' or a.value_depreciated != 0)
                {where_str} order by profile_id""".format(where_str=where_str)
        return sql


class AssetRegisterReportCompute(models.TransientModel):
    _inherit = 'report.asset.register'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'asset_register_xlsx'
        else:
            report_name = 'l10n_th_asset_register_report.' \
                          'report_asset_register_qweb'

        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)],
            limit=1).report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'l10n_th_asset_register_report.report_asset_register').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()
