import random
import string
from datetime import date, timedelta

from odoo.tests.common import TransactionCase


def code_generator(length=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choices(chars, k=length))


class TestL10nThSequence(TransactionCase):
    def setUp(self):
        super(TestL10nThSequence, self).setUp()

    def create_sequence(self, code=None, prefix=None, suffix=None):
        self.sequence_no += 1 if self.sequence_no else 1
        return self.env["ir.sequence"].create(
            {
                "name": f"test sequence {self.sequence}",
                "code": code,
                "prefix": prefix,
                "suffix": suffix,
            }
        )

    def create_sequence_date_range(self, sequence):
        date_from = date.today() - timedelta(days=random.randint(31, 365))
        date_to = date_from + timedelta(days=365)
        return self.env["ir.sequence.date_range"].create(
            {
                "date_from": date_from,
                "date_to": date_to,
                "sequence_id": sequence.id,
            }
        )

    def test_sequence_none(self):
        """Test no prefix and suffix"""
        code = code_generator()
        sequence = self.create_sequence(code)
        self.assertEqual(sequence.code, code)
        self.assertEqual(sequence.next_by_code(code), "1")
        self.assertEqual(sequence.next_by_code(code), "2")

    def test_sequence_year(self):
        """Test with year prefix and suffix"""
        code = code_generator()
        sequence = self.create_sequence(code, "PRE%%(year)s-")
        self.assertEqual(sequence.code, code)
        self.assertEqual(sequence.next_by_code(code), "PRE-1")
        self.assertEqual(sequence.next_by_code(code), "PRE-2")
