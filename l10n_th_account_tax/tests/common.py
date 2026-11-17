# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class ThAccountTaxCommon(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("th")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.revenue_account = cls.company_data["default_account_revenue"]
        cls.payable_account = cls.company_data["default_account_payable"]
        cls.receivable_account = cls.company_data["default_account_receivable"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.misc_journal = cls.company_data["default_journal_misc"]
        cls.sale_journal = cls.company_data["default_journal_sale"]
        (cls.partner_a + cls.partner_b).country_id = cls.env.ref("base.th")
        cls.partner_a.is_company = False
        cls.partner_b.is_company = True

        # ==== Payment methods, paid directly on the bank account ====
        cls.inbound_payment_method_line.payment_account_id = (
            cls.bank_journal.default_account_id
        )
        cls.outbound_payment_method_line.payment_account_id = (
            cls.bank_journal.default_account_id
        )

        # ==== Withholding tax accounts ====
        cls.wht_payable_account = cls._create_account(
            "Withholding Tax Payable Test", "215100", "liability_current"
        )
        cls.wht_base_account = cls._create_account(
            "Withholding Tax Base Test", "WHTBASE", "asset_current"
        )
        cls.company.withholding_tax_base_account_id = cls.wht_base_account

        # ==== VAT accounts and taxes ====
        cls.input_vat_acct = cls._create_account("V7", "V7", "liability_current")
        cls.output_vat_acct = cls._create_account("O7", "O7", "liability_current")
        cls.tax_group_vat = cls.env["account.tax.group"].create({"name": "VAT"})
        cls.input_vat = cls._create_vat_tax(
            "V7",
            "purchase",
            7.0,
            cls.input_vat_acct,
            tax_group=cls.tax_group_vat,
        )
        cls.output_vat = cls._create_vat_tax(
            "O7",
            "sale",
            7.0,
            cls.output_vat_acct,
            tax_group=cls.tax_group_vat,
        )

    @classmethod
    def _create_account(cls, name, code, account_type, **values):
        return cls.env["account.account"].create(
            {"name": name, "code": code, "account_type": account_type, **values}
        )

    @classmethod
    def _create_wht_tax(
        cls,
        name,
        amount=-3.0,
        type_tax_use="purchase",
        income_tax_type="hire_of_work",
        tax_accounts=None,
        **values,
    ):
        """Create a withholding tax.

        :param income_tax_type: standard income tax type of purchase taxes,
            by default hire of work, i.e. row 5 of the certificate
        :param tax_accounts: list of (account, factor percent) of the tax
            repartition, by default 100% on the withholding tax payable account
        :param values: other values of the tax, e.g. ``is_pit=True``
        """
        tax_accounts = tax_accounts or [(cls.wht_payable_account, 100.0)]
        tax_values = {
            "name": name,
            "amount": amount,
            "amount_type": "percent",
            "type_tax_use": type_tax_use,
            "is_withholding_tax": True,
            "l10n_th_income_tax_type": (
                income_tax_type if type_tax_use == "purchase" else False
            ),
            **values,
        }
        repartition_fields = (
            "invoice_repartition_line_ids",
            "refund_repartition_line_ids",
        )
        for field_name in repartition_fields:
            tax_values[field_name] = [
                Command.create({"repartition_type": "base"}),
                *[
                    Command.create(
                        {
                            "repartition_type": "tax",
                            "factor_percent": factor,
                            "account_id": account.id,
                        }
                    )
                    for account, factor in tax_accounts
                ],
            ]
        return cls.env["account.tax"].create(tax_values)

    @classmethod
    def _create_vat_tax(
        cls,
        name,
        type_tax_use,
        amount,
        tax_account,
        tax_group=None,
        exigibility="on_invoice",
        transition_account=None,
    ):
        """Create a VAT with a tax repartition line on the invoice.

        The refund repartition lines keep the Odoo default.

        :param exigibility: ``on_invoice`` or ``on_payment`` (undue VAT)
        :param transition_account: transition account of the undue VAT
        """
        values = {
            "name": name,
            "type_tax_use": type_tax_use,
            "amount_type": "percent",
            "amount": amount,
            "tax_exigibility": exigibility,
            "invoice_repartition_line_ids": [
                Command.create({"factor_percent": 100.0, "repartition_type": "base"}),
                Command.create(
                    {
                        "factor_percent": 100.0,
                        "repartition_type": "tax",
                        "account_id": tax_account.id,
                    }
                ),
            ],
        }
        if tax_group:
            values["tax_group_id"] = tax_group.id
        if transition_account:
            values["cash_basis_transition_account_id"] = transition_account.id
        return cls.env["account.tax"].create(values)

    @classmethod
    def _fill_tax_invoice(cls, move, number=None, date=None):
        """Fill in the tax invoice number and date of a vendor document."""
        move.tax_invoice_ids.write(
            {
                "tax_invoice_number": number or f"TINV-{move.id:05d}",
                "tax_invoice_date": date or move.date,
            }
        )

    @classmethod
    def _create_th_invoice(
        cls,
        move_type,
        lines,
        partner=None,
        date=None,
        currency=None,
        post=False,
        fill_tax_invoice=False,
    ):
        """Create an invoice, a bill or a credit note.

        :param lines: list of ``(price_unit, taxes)`` or
            ``(price_unit, taxes, account)``, by default the revenue account
            for customer documents and the expense account for vendor ones
        :param date: invoice and accounting date, by default today
        :param fill_tax_invoice: fill in the tax invoice of the document
        """
        date = date or fields.Date.today()
        default_account = (
            cls.revenue_account if move_type.startswith("out_") else cls.expense_account
        )
        invoice_lines = []
        for index, line in enumerate(lines, start=1):
            price_unit, taxes = line[:2]
            account = line[2] if len(line) > 2 else default_account
            invoice_lines.append(
                Command.create(
                    {
                        "name": f"Test line {index}",
                        "account_id": account.id,
                        "quantity": 1.0,
                        "price_unit": price_unit,
                        "tax_ids": [Command.set(taxes.ids)],
                    }
                )
            )
        values = {
            "move_type": move_type,
            "partner_id": (partner or cls.partner_a).id,
            "invoice_date": date,
            "date": date,
            "invoice_line_ids": invoice_lines,
        }
        if currency:
            values["currency_id"] = currency.id
        move = cls.env["account.move"].create(values)
        if fill_tax_invoice and move.tax_invoice_ids:
            cls._fill_tax_invoice(move)
        if post:
            move.action_post()
        return move

    def _create_entry(self, lines, journal=None, date=None, **values):
        """Create a journal entry.

        :param lines: list of values of the journal items
        :param journal: by default the miscellaneous journal
        :param date: accounting date, by default today
        :param values: other values of the entry, e.g. ``partner_id``
        """
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": (journal or self.misc_journal).id,
                "date": date or fields.Date.today(),
                "line_ids": [Command.create(line) for line in lines],
                **values,
            }
        )

    def _create_tax_entry(
        self, tax, partner_amounts=None, journal=None, date=None, **values
    ):
        """Create an entry with an expense taxed by ``tax`` and its payable.

        :param partner_amounts: list of ``(partner, base amount)``, by default
            1000 for ``partner_a``
        """
        partner_amounts = partner_amounts or [(self.partner_a, 1000.0)]
        net_factor = 1.0 + tax.amount / 100.0
        lines = []
        for partner, base in partner_amounts:
            lines.extend(
                [
                    {
                        "name": "Service expense",
                        "partner_id": partner.id,
                        "account_id": self.expense_account.id,
                        "debit": base,
                        "tax_ids": [Command.set(tax.ids)],
                    },
                    {
                        "name": "Net payable",
                        "partner_id": partner.id,
                        "account_id": self.payable_account.id,
                        "credit": base * net_factor,
                        "tax_ids": [Command.set([])],
                    },
                ]
            )
        return self._create_entry(lines, journal=journal, date=date, **values)

    def _create_payment_register(self, moves, withhold=None, inbound=False, **values):
        """Create the payment register wizard on the bank journal.

        :param withhold: ``withhold_pay`` or ``withhold`` (no liquidity), by
            default the one proposed by the wizard
        :param inbound: use the inbound payment method, e.g. for a refund
        :param values: other values of the wizard, e.g. ``amount``
        """
        wizard_values = {"payment_date": fields.Date.today()}
        if withhold:
            wizard_values["withhold"] = withhold
        if withhold != "withhold":
            payment_method_line = (
                self.inbound_payment_method_line
                if inbound
                else self.outbound_payment_method_line
            )
            wizard_values.update(
                {
                    "journal_id": self.bank_journal.id,
                    "payment_method_line_id": payment_method_line.id,
                }
            )
        wizard_values.update(values)
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=moves.ids)
            .create(wizard_values)
        )

    def _pay(self, moves, wizard=None, **values):
        """Create the payment of the moves, with the given wizard if any."""
        wizard = wizard or self._create_payment_register(moves, **values)
        payment = wizard._create_payments()
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.move_id.state, "posted")
        return payment

    def _assert_withholding_lines(self, record, expected):
        """Check the withholding lines of a wizard or a payment.

        :param expected: list of ``(tax, base amount, withholding amount)``
        """
        self.assertEqual(len(record.withholding_line_ids), len(expected))
        for tax, base, amount in expected:
            self.assertRecordValues(
                record.withholding_line_ids.filtered_domain([("tax_id", "=", tax.id)]),
                [{"tax_id": tax.id, "base_amount": base, "amount": amount}],
            )
