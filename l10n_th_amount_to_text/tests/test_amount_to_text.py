# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase

from .. import pre_init_hook


class TestAmountToText(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.th_lang = cls.env.ref("base.lang_th")

    def test_01_currency_th_amount_to_text(self):
        """verify that amount_to_text converted text to thai language"""
        currency = self.env.ref("base.THB")
        amount = 1050.75
        amount_text_en = currency.amount_to_text(amount)
        self.assertEqual(
            amount_text_en, "One Thousand And Fifty Baht and Seventy-Five Satang"
        )
        amount_text_th = currency.with_context(lang="th_TH").amount_to_text(amount)
        self.assertEqual(amount_text_th, "หนึ่งพันห้าสิบบาทเจ็ดสิบห้าสตางค์")

    def test_02_currency_eur_amount_to_text(self):
        """verify that amount_to_text works as expected"""
        currency = self.env.ref("base.EUR")
        amount = 1050.75
        amount_text_eur = currency.amount_to_text(amount)
        self.assertEqual(
            amount_text_eur, "One Thousand And Fifty Euros and Seventy-Five Cents"
        )
        amount_text_eur = currency.with_context(lang="th_TH").amount_to_text(amount)
        self.assertEqual(amount_text_eur, "หนึ่งพันห้าสิบยูโรเจ็ดสิบห้าเซนต์")

    def test_03_pre_init_hook(self):
        """If not activate Thai Language. It will auto activate."""
        self.th_lang.write({"active": False})
        self.assertFalse(self.th_lang.active)
        pre_init_hook(self.env)
        self.assertTrue(self.th_lang.active)
        # Nothing to do
        pre_init_hook(self.env)
        self.assertTrue(self.th_lang.active)
