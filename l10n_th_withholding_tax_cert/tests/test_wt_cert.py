# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SingleTransactionCase
from odoo.tests.common import Form
from odoo.exceptions import ValidationError


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
            'wt_account': True,
        })
        # Journals
        cls.journal_bank = cls.env['account.journal'].create(
            {'name': 'Bank', 'type': 'bank', 'code': 'BNK67'})
        cls.journal_purchase = cls.env['account.journal'].search(
            [('type', '=', 'purchase')])[0]
        # Prepare Supplier Invoices
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
                'price_unit': 100.00, })]
        }
        cls.supplier_invoice_wt = \
            cls.env['account.invoice'].create(invoice_dict)

    def test_wt_cert(self):
        """ Supplier Invoice to Payment to WT Cert """
        # User have not filled in Tax Invoice / Date in account_invoice_tax
        self.supplier_invoice_wt.action_invoice_open()
        # Payment by writeoff with withholding tax account
        ctx = {'active_ids': [self.supplier_invoice_wt.id],
               'active_id': self.supplier_invoice_wt.id,
               'active_model': 'account.invoice'}
        PaymentWizard = self.env['account.payment']
        view_id = ('account.view_account_payment_invoice_form')
        with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
            f.amount = 97.0  # To withhold 3.0
            f.journal_id = self.journal_bank
            f.payment_difference_handling = 'reconcile'
            f.writeoff_account_id = self.wt_account_payable
            f.writeoff_label = 'Withhold 3%'
        payment = f.save()
        payment.action_validate_invoice_payment()
        self.assertEqual(payment.state, 'posted')
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
        with Form(WTCert.with_context(ctx_cert)) as f:
            f.income_tax_form = 'pnd3'
        cert = f.save()
        self.assertRecordValues(
            cert.wt_line, [{'amount': 3.0}])
        with self.assertRaises(ValidationError):
            cert.wt_line[0].wt_percent = 3.0
        cert.wt_line[0]._onchange_wt_percent()
        self.assertEqual(cert.wt_line[0].base, 100.0)
