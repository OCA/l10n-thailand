import datetime

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestIrSequenceBeStandard(SingleTransactionCase):
    """ A few tests for a 'Standard' sequence. """

    def test_ir_sequence_be_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_be",
                "name": "Test sequence BE",
                "use_date_range": False,
                "prefix": "test-%(year_be)s/%(y_be)s-",
                "suffix": "-%(year_be)s/%(y_be)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

    def test_ir_sequence_be_2_check_year(self):
        year = fields.Date.today().year
        y_be = (year + 543) % 100
        date1 = datetime.date(year=year - 1, month=11, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_be")
        self.assertEqual(
            value, f"test-{year+543-1}/{y_be-1}-0001-{year+543-1}/{y_be-1}"
        )
        value = seq1.next_by_code("test_be")
        self.assertEqual(
            value, f"test-{year+543-1}/{y_be-1}-0002-{year+543-1}/{y_be-1}"
        )

        date2 = datetime.date(year=year, month=3, day=14)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_be")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0003-{year+543}/{y_be}")
        value = seq2.next_by_code("test_be")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0004-{year+543}/{y_be}")

    def test_ir_sequence_be_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_be")])
        seq.unlink()


class TestIrSequenceBeDateRange(SingleTransactionCase):
    """ A few tests for a 'Standard' sequence with date_range. """

    def test_ir_sequence_be_date_range_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_be_date_range",
                "name": "Test sequence date_range BE",
                "use_date_range": True,
                "prefix": "test-%(range_year_be)s/%(range_y_be)s-",
                "suffix": "-%(range_year_be)s/%(range_y_be)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

        year = fields.Date.today().year
        date_range_1 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year - 1, month=11, day=1),
                "date_to": datetime.date(year=year, month=1, day=31),
                "sequence_id": seq.id,
                "number_next_actual": 314,
            }
        )
        self.assertTrue(date_range_1)

        date_range_2 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year, month=2, day=1),
                "date_to": datetime.date(year=year, month=4, day=30),
                "sequence_id": seq.id,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(date_range_2)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(domain)
        self.assertEqual(len(date_ranges), 2)

    def test_ir_sequence_be_date_range_2_check_year(self):
        year = fields.Date.today().year
        y_be = (year + 543) % 100
        date1 = datetime.date(year=year - 1, month=11, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_be_date_range")
        self.assertEqual(
            value, f"test-{year+543-1}/{y_be-1}-0314-{year+543-1}/{y_be-1}"
        )
        value = seq1.next_by_code("test_be_date_range")
        self.assertEqual(
            value, f"test-{year+543-1}/{y_be-1}-0315-{year+543-1}/{y_be-1}"
        )

        date2 = datetime.date(year=year, month=3, day=14)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_be_date_range")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0042-{year+543}/{y_be}")
        value = seq2.next_by_code("test_be_date_range")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0043-{year+543}/{y_be}")

    def test_ir_sequence_be_date_range_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_be_date_range")])
        seq.unlink()


class TestIrSequenceBeRangeEnd(SingleTransactionCase):
    """ A few tests for a 'Standard' sequence with range end. """

    def test_ir_sequence_be_range_end_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_be_range_end",
                "name": "Test sequence range end BE",
                "use_date_range": True,
                "prefix": "test-%(range_end_year_be)s/%(range_end_y_be)s-",
                "suffix": "-%(range_end_year_be)s/%(range_end_y_be)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

        year = fields.Date.today().year
        date_range_1 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year - 1, month=11, day=1),
                "date_to": datetime.date(year=year, month=1, day=31),
                "sequence_id": seq.id,
                "number_next_actual": 314,
            }
        )
        self.assertTrue(date_range_1)

        date_range_2 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year, month=2, day=1),
                "date_to": datetime.date(year=year, month=4, day=30),
                "sequence_id": seq.id,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(date_range_2)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(domain)
        self.assertEqual(len(date_ranges), 2)

    def test_ir_sequence_be_range_end_2_check_year(self):
        year = fields.Date.today().year
        y_be = (year + 543) % 100
        date1 = datetime.date(year=year - 1, month=11, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_be_range_end")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0314-{year+543}/{y_be}")
        value = seq1.next_by_code("test_be_range_end")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0315-{year+543}/{y_be}")

        date2 = datetime.date(year=year, month=3, day=14)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_be_range_end")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0042-{year+543}/{y_be}")
        value = seq2.next_by_code("test_be_range_end")
        self.assertEqual(value, f"test-{year+543}/{y_be}-0043-{year+543}/{y_be}")

    def test_ir_sequence_be_range_end_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_be_range_end")])
        seq.unlink()
