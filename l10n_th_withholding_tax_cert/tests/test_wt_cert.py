# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.tests.common import SingleTransactionCase
from odoo.tests.common import Form


class TestWTCert(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestWTCert, cls).setUpClass()
        # Accounts
        type_asset = cls.env.ref('account.data_account_type_current_assets')
        cls.wt_account_payable = cls.env['account.account'].create({
            'name': 'SUP_WT_3',
            'code': 'SUPWT3',
            'user_type_id': type_asset.id,
        })
        cls.wt_account_receivable = cls.env['account.account'].create({
            'name': 'CUST_WT_3',
            'code': 'CUSTWT3',
            'user_type_id': type_asset.id,
        })
        # Journals
        cls.journal_misc = cls.env['account.journal'].search(
            [('type', '=', 'general')])[0]
        cls.journal_bank = cls.env['account.journal'].create(
            {'name': 'Bank', 'type': 'bank', 'code': 'BNK67'})
        cls.journal_purchase = cls.env['account.journal'].search(
            [('type', '=', 'purchase')])[0]
        # Payment Methods
        cls.payment_method_manual_out = \
            cls.env.ref('account.account_payment_method_manual_out')
        # Payments
        vals_payment = {
            'name': "",
            'line_ids': [(0, 0, {'value': 'balance', 'days': 15})]
            }
        cls.payment_term_15 = cls.env['account.payment.term'].create(
            vals_payment)
        # Withholding tax
        wt_vals = {
            'name': 'Code 1040',
            'code': '1040',
            'certification': True,
            'account_receivable_id': cls.wt_account_receivable.id,
            'account_payable_id': cls.wt_account_payable.id,
            'journal_id': cls.journal_misc.id,
            'payment_term': cls.payment_term_15.id,
            'rate_ids': [(0, 0, {'tax': 3.00, 'base': 1.00})]
        }
        cls.wt = cls.env['withholding.tax'].create(wt_vals)

        # Prepare Supplier Invoices WT
        payable_account = cls.env['account.account'].search(
            [('user_type_id', '=', cls.env.ref(
                'account.data_account_type_payable').id)],
            limit=1, order='id')
        expense_account = cls.env['account.account'].search(
            [('user_type_id', '=', cls.env.ref(
                'account.data_account_type_expenses').id)],
            limit=1)
        invoice_dict = {
            'name': 'Test Supplier Invoice WT',
            'partner_id': cls.env.ref('base.res_partner_12').id,
            'journal_id': cls.journal_purchase.id,
            'account_id': payable_account.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'account_id': expense_account.id,
                'name': 'Advice',
                'price_unit': 100.00,
                'invoice_line_tax_wt_ids': [(6, 0, [cls.wt.id])]})]
        }
        cls.supplier_invoice_wt = \
            cls.env['account.invoice'].create(invoice_dict)
        cls.supplier_invoice_wt._onchange_invoice_line_wt_ids()  # WT Tax Line

    def test_wt_cert(self):
        """ Supplier Invoice to Payment to WT Cert (Full) """
        # User have not filled in Tax Invoice / Date in account_invoice_tax
        self.supplier_invoice_wt.action_invoice_open()
        # Make full payment from invoice
        payment = self.env['account.payment'].create({
            'payment_date': fields.Date.today(),
            'payment_type': 'outbound',
            'amount': 97.00,  # Withhold 3.00
            'journal_id': self.journal_bank.id,
            'partner_type': 'supplier',
            'partner_id': self.env.ref('base.res_partner_12').id,
            'payment_method_id': self.payment_method_manual_out.id,
            'invoice_ids': [(4, self.supplier_invoice_wt.id, None)],
        })
        payment.post()
        # Create WT Cert from Payment's Action Wizard
        ctx = {'active_id': payment.id, 'active_ids': [payment.id]}
        f = Form(self.env['create.withholding.tax.cert'].with_context(ctx))
        wizard = f.save()
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get('context')
        ctx_cert.update({'default_income_tax_form': 'pnd3',
                         'wt_cert_income_type': '1'})
        WTCert = self.env['withholding.tax.cert']
        f = Form(WTCert.with_context(ctx_cert))
        cert = f.save()
        self.assertRecordValues(
            cert.wt_line, [{'wt_percent': 3.0, 'base': 100.0, 'amount': 3.0}])
