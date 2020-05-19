# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from num2words import num2words

from odoo.tests.common import SavepointCase


class TestAmountToText(SavepointCase):
    def test_01_currency_th_amount_to_text(self):
        """ verify that amount_to_text converted text to thai language """
        currency = self.env.ref("base.THB")
        amount = 1050.75
        amount_text_en = currency.amount_to_text(amount)
        self.assertEqual(
            amount_text_en, "One Thousand And Fifty Baht and Seventy-Five Satang"
        )
        amount_text_th = currency.with_context({"lang": "th_TH"}).amount_to_text(amount)
        try:
            # check version num2words need 0.5.7+
            num2words(amount, to="currency", lang="th")
            self.assertEqual(amount_text_th, "หนึ่งพันห้าสิบบาทเจ็ดสิบห้าสตางค์")
        except NotImplementedError:
            # num2words version 0.5.6 (core odoo)
            self.assertEqual(
                amount_text_th, "one thousand and fifty euro, seventy-five cents"
            )

    def test_02_currency_eur_amount_to_text(self):
        """ verify that amount_to_text works as expected """
        currency = self.env.ref("base.EUR")
        amount = 1050.75
        amount_text_eur = currency.amount_to_text(amount)
        self.assertEqual(
            amount_text_eur, "One Thousand And Fifty Euros and Seventy-Five Cents"
        )
