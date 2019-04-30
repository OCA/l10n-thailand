# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase


class TestAccountBilling(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Model
        Journal = cls.env['account.journal']

        # Get required Model data
        cls.journal_sale = Journal.search([('type', '=', 'sale')])[0]

        invoice_dict = {
            'name': 'Test Customer Invoice',
            'partner_id': cls.env.ref('base.res_partner_12').id,
            'journal_id': cls.journal_sale.id,
            'account_id': cls.env['account.account'].search(
                [('user_type_id', '=', cls.env.ref(
                    'account.data_account_type_receivable').id)],
                limit=1, order='id').id,
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'account_id': cls.env['account.account'].search(
                    [('user_type_id', '=', cls.env.ref(
                        'account.data_account_type_revenue').id)],
                    limit=1).id,
                'name': 'Advice',
                'price_unit': 100.00})]
        }
        cls.customer_invoice = \
            cls.env['account.invoice'].create(invoice_dict)
        cls.customer_invoice.action_invoice_open()

    def test_create_billing_case(self):
        ctx = {'active_id': self.customer_invoice.id,
               'active_ids': [self.customer_invoice.id],
               'bill_type': 'out_invoice'}
        customer_billing = \
            self.env['account.billing'].with_context(ctx).create({})
        customer_billing.validate_billing()
        self.assertEquals(customer_billing.invoice_ids.amount_total, 100.0)
        self.assertEquals(customer_billing.invoice_related_count, 1.0)
